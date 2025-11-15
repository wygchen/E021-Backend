#!/usr/bin/env python3
"""
Experience Planning Agent with RAG Integration

This agent implements the PlannerAgent from full_idea.md, using RAG tools
to find destinations and experiences that match the user's travel profile.
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext

from app.rag_tools import get_rag_toolkit


class ExperiencePlanningAgent(BaseAgent):
    """
    The PlannerAgent: Translates user_travel_profile into concrete travel plans using RAG.
    
    This agent does not talk to the user directly. It analyzes the user profile
    and uses RAG tools to:
    1. Find 3 distinct travel destinations
    2. Find 4 unique experiences for each destination
    3. Build a complete plan or identify conflicts that need user clarification
    
    Outputs either:
    - SUCCESS: A complete plan with 3 destinations and their experiences
    - CONFLICT: A question to resolve competing options
    """
    
    def __init__(self, name: str = "ExperiencePlanningAgent"):
        super().__init__(name=name)
    
    def _get_rag_toolkit(self):
        """Get the RAG toolkit instance (lazy loaded)."""
        return get_rag_toolkit()
    
    def _extract_profile_keywords(self, profile: str) -> str:
        """Extract search keywords from user profile."""
        # Simple extraction - in production, could use LLM to parse
        return profile
    
    def _build_search_strategy(self, profile: str, qa_history: List[Dict]) -> Dict[str, Any]:
        """
        Determine search strategy based on user profile.
        
        Returns:
            dict with 'approach' (top-down or bottom-up) and 'query' info
        """
        # Check if profile mentions specific experiences/events (bottom-up triggers)
        profile_lower = profile.lower()
        bottom_up_keywords = [
            'concert', 'festival', 'k-pop', 'event', 'show',
            'elephant', 'safari', 'diving', 'skiing'
        ]
        
        has_anchor = any(keyword in profile_lower for keyword in bottom_up_keywords)
        
        if has_anchor:
            return {
                'approach': 'bottom-up',
                'query': profile,
                'reason': 'User has specific experience anchor'
            }
        else:
            return {
                'approach': 'top-down',
                'query': profile,
                'reason': 'User has general preferences'
            }
    
    def _select_best_experiences(
        self,
        experiences: List[Dict[str, Any]],
        destination_id: str,
        count: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Select the best experiences for a destination, prioritizing Anchor Events.
        
        Args:
            experiences: List of experience dossiers
            destination_id: The destination ID
            count: Number of experiences to select
        
        Returns:
            Selected experiences with role diversity
        """
        # Filter to this destination
        dest_experiences = [
            exp for exp in experiences
            if exp.get('parent_destination_id') == destination_id
        ]
        
        if not dest_experiences:
            return []
        
        # Prioritize by itinerary_role
        role_priority = {
            'Anchor-Event': 0,
            'Secondary-Highlight': 1,
            'Add-On': 2
        }
        
        # Sort by role priority
        sorted_exp = sorted(
            dest_experiences,
            key=lambda x: role_priority.get(x.get('itinerary_role', 'Add-On'), 3)
        )
        
        # Select top experiences ensuring role diversity
        selected = []
        roles_used = set()
        
        # First pass: get one of each role type
        for exp in sorted_exp:
            role = exp.get('itinerary_role', 'Add-On')
            if role not in roles_used and len(selected) < count:
                selected.append(exp)
                roles_used.add(role)
        
        # Second pass: fill remaining slots
        for exp in sorted_exp:
            if exp not in selected and len(selected) < count:
                selected.append(exp)
        
        return selected[:count]
    
    def _detect_conflicts(
        self,
        experiences: List[Dict[str, Any]],
        profile: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if there are competing Anchor-Event experiences that create a conflict.
        
        Returns:
            Conflict dict with 'conflict_question' or None if no conflict
        """
        # Find Anchor-Event experiences
        anchors = [
            exp for exp in experiences
            if exp.get('itinerary_role') == 'Anchor-Event'
        ]
        
        # If we have multiple high-scoring anchor events for same destination, it's a conflict
        if len(anchors) >= 2:
            # Check if they're competing (same destination, similar scores)
            dest_groups = {}
            for anchor in anchors:
                dest_id = anchor.get('parent_destination_id')
                if dest_id:
                    dest_groups.setdefault(dest_id, []).append(anchor)
            
            # Find conflicts within same destination
            for dest_id, dest_anchors in dest_groups.items():
                if len(dest_anchors) >= 2:
                    # Use conflict_solver from the experience dossier
                    conflict_data = dest_anchors[0].get('conflict_solver', {})
                    conflict_question = conflict_data.get('conflict_question')
                    
                    if conflict_question:
                        return {
                            'conflict_question': conflict_question,
                            'competing_experiences': [exp['experience_id'] for exp in dest_anchors]
                        }
        
        return None
    
    def _format_plan_output(
        self,
        destinations: List[Dict[str, Any]],
        experiences_by_dest: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Format the final plan output for the user.
        
        Returns:
            Plan dict with status: SUCCESS and formatted destinations
        """
        formatted_destinations = []
        
        for dest in destinations:
            dest_id = dest['destination_id']
            dest_experiences = experiences_by_dest.get(dest_id, [])
            
            # Format experiences
            formatted_experiences = []
            for exp in dest_experiences:
                formatted_experiences.append({
                    'title': exp['experience_name'],
                    'short_description': exp.get('itinerary_pitch_text', exp.get('one_line_pitch', '')),
                    'cost_tier': exp.get('cost_tier', 'Mid-Range'),
                    'duration': exp.get('duration_type', 'Unknown'),
                    'role': exp.get('itinerary_role', 'Add-On')
                })
            
            formatted_destinations.append({
                'name': dest['destination_name'],
                'destination_id': dest_id,
                'summary': dest.get('one_line_pitch', ''),
                'archetype': dest.get('primary_archetype', ''),
                'cost_index': dest.get('cost_index', 3),
                'experiences': formatted_experiences
            })
        
        return {
            'status': 'SUCCESS',
            'data': formatted_destinations
        }
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Main agent logic: analyze profile and generate plan using RAG.
        """
        # Get RAG toolkit
        rag_toolkit = self._get_rag_toolkit()
        
        # Get user profile from session state
        state = ctx.session.state
        profile = state.get('user_travel_profile', '')
        qa_history = state.get('qa_history', [])
        
        # If no profile yet, can't plan
        if not profile or profile == '':
            state['experience_planning_result'] = {
                'status': 'INSUFFICIENT',
                'message': 'No user profile available yet'
            }
            yield Event(author=self.name)
            return
        
        try:
            # Determine search strategy
            strategy = self._build_search_strategy(profile, qa_history)
            
            if strategy['approach'] == 'top-down':
                # Search destinations first
                destinations = rag_toolkit.search_destinations(
                    query=strategy['query'],
                    top_k=3
                )
                
                # Then search experiences for each destination
                all_experiences = []
                for dest in destinations:
                    dest_id = dest['destination_id']
                    dest_experiences = rag_toolkit.search_experiences(
                        query=profile,
                        destination_id=dest_id,
                        top_k=7
                    )
                    all_experiences.extend(dest_experiences)
            
            else:  # bottom-up
                # Search experiences first
                all_experiences = rag_toolkit.search_experiences(
                    query=strategy['query'],
                    top_k=15
                )
                
                # Extract unique destination IDs
                dest_ids = list(set(
                    exp['parent_destination_id']
                    for exp in all_experiences
                    if 'parent_destination_id' in exp
                ))[:3]
                
                # Get destination details
                destinations = rag_toolkit.search_destinations(
                    destination_ids=dest_ids
                )
            
            # Check for conflicts
            conflict = self._detect_conflicts(all_experiences, profile)
            if conflict:
                state['experience_planning_result'] = {
                    'status': 'CONFLICT',
                    'data': conflict
                }
                yield Event(author=self.name)
                return
            
            # Select best experiences for each destination
            experiences_by_dest = {}
            for dest in destinations:
                dest_id = dest['destination_id']
                selected = self._select_best_experiences(
                    all_experiences,
                    dest_id,
                    count=4
                )
                experiences_by_dest[dest_id] = selected
            
            # Build final plan
            plan = self._format_plan_output(destinations, experiences_by_dest)
            state['experience_planning_result'] = plan
            
            yield Event(author=self.name)
        
        except Exception as e:
            # Handle errors gracefully
            state['experience_planning_result'] = {
                'status': 'ERROR',
                'message': f'Failed to generate plan: {str(e)}'
            }
            yield Event(author=self.name)

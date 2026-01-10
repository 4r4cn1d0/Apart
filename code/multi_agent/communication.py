"""
Communication System for Multi-Agent Platform

Manages:
- Public chat (all agents see)
- Private DMs (pairwise)
- Message logging
- Communication history
"""

from typing import List, Dict, Optional
from .agent_base import Message


class CommunicationChannel:
	"""
	Manages communication between agents.
	"""
	
	def __init__(self):
		self.public_messages: List[Message] = []
		self.private_messages: Dict[str, List[Message]] = {}  # agent_id -> messages
		self.all_messages: List[Message] = []
	
	def send_public_message(self, message: Message):
		"""Send a public message (all agents see)"""
		if message.receiver_id is not None:
			raise ValueError("Public message must have receiver_id=None")
		
		message.message_type = "public"
		self.public_messages.append(message)
		self.all_messages.append(message)
	
	def send_private_message(self, message: Message):
		"""Send a private message (only recipient sees)"""
		if message.receiver_id is None:
			raise ValueError("Private message must have receiver_id")
		
		message.message_type = "private"
		
		# Store in recipient's inbox
		if message.receiver_id not in self.private_messages:
			self.private_messages[message.receiver_id] = []
		self.private_messages[message.receiver_id].append(message)
		
		# Also store in sender's outbox (optional, for logging)
		self.all_messages.append(message)
	
	def get_messages_for_agent(
		self,
		agent_id: str,
		include_private: bool = True,
		recent_only: bool = True,
		max_messages: Optional[int] = None
	) -> List[Message]:
		"""
		Get all messages visible to an agent.
		
		Args:
			agent_id: Agent to get messages for
			include_private: Include private messages sent to this agent
			recent_only: Only return messages from current day
			max_messages: Limit number of messages returned
		"""
		messages = []
		
		# Public messages (everyone sees)
		messages.extend(self.public_messages)
		
		# Private messages (only if recipient)
		if include_private and agent_id in self.private_messages:
			messages.extend(self.private_messages[agent_id])
		
		# Sort by timestamp
		messages.sort(key=lambda m: m.timestamp)
		
		# Apply limits
		if max_messages:
			messages = messages[-max_messages:]
		
		return messages
	
	def get_recent_public_messages(self, since_timestamp: int = 0) -> List[Message]:
		"""Get public messages since a timestamp"""
		return [m for m in self.public_messages if m.timestamp >= since_timestamp]
	
	def get_all_messages(self) -> List[Message]:
		"""Get all messages (for logging/analysis)"""
		return self.all_messages.copy()
	
	def clear_day_messages(self, day: int):
		"""Clear messages from a specific day (optional cleanup)"""
		# Usually we keep all messages for analysis
		pass

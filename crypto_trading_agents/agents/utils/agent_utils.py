"""Utility functions for agent nodes."""

from langchain_core.messages import HumanMessage, RemoveMessage


def create_msg_delete():
    """Create a node that clears messages to manage context window."""
    def delete_messages(state):
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        placeholder = HumanMessage(content="Continue")
        return {"messages": removal_operations + [placeholder]}
    return delete_messages

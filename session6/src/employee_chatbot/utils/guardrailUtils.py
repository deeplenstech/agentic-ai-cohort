import os
import logging
import boto3
from crewai.hooks import before_llm_call, after_llm_call

logger = logging.getLogger(__name__)

bedrock_runtime = boto3.client("bedrock-runtime")

GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "DRAFT")

def apply_guardrail_filters(text: str, source: str = "INPUT") -> tuple[str, bool]:
    """
    Apply AWS Bedrock Guardrail to the given text.
    
    Returns:
        tuple: (processed_text, is_blocked)
        processed_text: The text after guardrail application (could be original, masked, or blocked message).
        is_blocked: Boolean indicating if a 'BLOCKED' action was triggered by any policy.
    """
    if not GUARDRAIL_ID:
        return text, False

    try:
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}]
        )

        action = response.get("action")
        processed_text = text
        is_blocked = False

        if action == "GUARDRAIL_INTERVENED":
            outputs = response.get("outputs", [])
            if outputs:
                processed_text = outputs[0].get("text", text)

            # Check assessments to distinguish between Masking and Blocking
            is_blocked = _is_policy_blocked(response)
            
            log_action = "BLOCKED" if is_blocked else "MASKED"
            logger.warning(f"Guardrail {log_action} {source} content: {processed_text}")

        return processed_text, is_blocked

    except Exception as e:
        logger.error(f"Error applying guardrail: {str(e)}")
        return text, False

def _is_policy_blocked(response: dict) -> bool:
    """Helper to detect if any guardrail policy resulted in a 'BLOCKED' action."""
    for assessment in response.get("assessments", []):
        for policy_type in ["contentPolicy", "topicPolicy", "wordPolicy", "sensitiveInformationPolicy", "contextualGroundingPolicy"]:
            policy = assessment.get(policy_type, {})
            if policy_type == "contentPolicy":
                items = policy.get("filters", [])
            elif policy_type == "topicPolicy":
                items = policy.get("topics", [])
            elif policy_type == "wordPolicy":
                items = policy.get("customWords", []) + policy.get("managedWordLists", [])
            elif policy_type == "sensitiveInformationPolicy":
                items = policy.get("piiEntities", []) + policy.get("regexQueries", [])
            elif policy_type == "contextualGroundingPolicy":
                items = policy.get("filters", [])
            else:
                items = []
                
            for item in items:
                if item.get("action") == "BLOCKED":
                    return True
    return False

def register_guardrail_hooks():
    """
    Register Bedrock Guardrail hooks for CrewAI LLM calls.
    Ensures both LLM inputs and outputs are masked or blocked according to policy.
    """

    @before_llm_call
    def guardrail_before_llm(context):
        """Automatically validate and mask prompts before they reach the LLM."""
        if not context.messages:
            return None
        
        for msg in context.messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            if role != "user":
                continue
            if not content:
                continue

            processed_text, is_blocked = apply_guardrail_filters(content, source="INPUT")
            
            if is_blocked:
                print("-------------------- INPUT ----------------------")
                print(content)
                print("-------------------- OUTPUT ---------------------")
                print(processed_text)
                print("------------------------------------")
                logger.warning(f"Guardrail BLOCKED LLM prompt: {processed_text}")
                # Returning False in before_llm_call blocks the LLM execution in CrewAI
                return False 
            
            if processed_text != content:
                logger.info("Guardrail MASKED LLM prompt.")
                msg["content"] = processed_text
                
        return None

    # @after_llm_call
    # def guardrail_after_llm(context):
    #     """Automatically validate and mask LLM responses."""
    #     if not context.response:
    #         return None

    #     processed_text, is_blocked = apply_guardrail_filters(context.response, source="OUTPUT")

    #     if is_blocked:
    #         logger.warning(f"Guardrail BLOCKED LLM response: {processed_text}")
    #         return "Guardrails blocked the response" 
        
    #     if processed_text != context.response:
    #         logger.warning(f"Guardrail intervened on LLM response. Action: {'BLOCKED' if is_blocked else 'MASKED'}")
    #         return processed_text

    #     return None
# Azure imports
from azure.identity import DefaultAzureCredential
from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
from pyrit.prompt_target import OpenAIChatTarget
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# Azure AI Project Information
azure_ai_project = os.getenv("FOUNDRY_ENDPOINT")

# Instantiate your AI Red Teaming Agent
red_team_agent = RedTeam(
    azure_ai_project=azure_ai_project,
    credential=DefaultAzureCredential(),
    risk_categories=[
        RiskCategory.Violence,
        RiskCategory.HateUnfairness,
        RiskCategory.Sexual,
        RiskCategory.SelfHarm
    ],
    num_objectives=5,
)

red_team_agent_attack_prompts = RedTeam(
    azure_ai_project=azure_ai_project,
    credential=DefaultAzureCredential(),
    custom_attack_seed_prompts="data/custom_attack_prompts.json",
)

# Configuration of a dummy
def test_chat_target(query: str) -> str:
    return "I am a simple AI assistant that follows ethical guidelines. I'm sorry, Dave. I'm afraid I can't do that."

# Configuration for Azure OpenAI model (foundational model)
azure_openai_config = { 
    "azure_endpoint": f"{os.environ.get('gpt_endpoint')}/openai/deployments/{os.environ.get('gpt_deployment')}/chat/completions",
    "api_key": os.environ.get("FOUNDRY_KEY"),
    "azure_deployment": os.environ.get("gpt_deployment")
}


# Configuration for Azure OpenAI Chat Target (could be based on fine-tuned custom model)
chat_target = OpenAIChatTarget(
    model_name=os.environ.get("gpt_deployment"),
    endpoint=f"{os.environ.get("gpt_endpoint")}/openai/deployments/{os.environ.get('gpt_deployment')}/chat/completions" ,
    api_key=os.environ.get("gpt_api_key"),
    api_version=os.environ.get("gpt_api_version"),
)

async def main():
    ## Simple scan using a dummy target function
    #red_team_result = await red_team_agent.scan(target=test_chat_target)
    
    ## Scan using Azure OpenAI foundational model as target
    #red_team_result = await red_team_agent.scan(target=azure_openai_config)
    
    ## Scan using Azure OpenAI Chat Target (could be based on fine-tuned custom model)
    #red_team_result = await red_team_agent.scan(target=chat_target)
    
    ## Scan using Azure OpenAI Chat Target with  and multiple strategies (EASY)
    # red_team_result = await red_team_agent.scan(
    #     target=chat_target,
    #     scan_name="Red Team Scan - Easy Strategies",
    #     attack_strategies=[
    #         AttackStrategy.EASY
    #     ])    
    
    ## Scan using Azure OpenAI Chat Target with  and multiple strategies (MEDIUM)
    red_team_result = await red_team_agent.scan(
        target=chat_target,
        scan_name="Red Team Scan - Easy-Moderate Strategies",
        attack_strategies=[
            AttackStrategy.Flip,
            AttackStrategy.ROT13,
            AttackStrategy.Base64,
            AttackStrategy.AnsiAttack,
            AttackStrategy.Tense
        ])    

    ## Scan using Azure OpenAI Chat Target with custom attack prompts
    #red_team_result = await red_team_agent_attack_prompts.scan(target=chat_target) 

asyncio.run(main())



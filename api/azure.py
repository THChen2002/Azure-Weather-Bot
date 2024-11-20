import os
#Azure CLU
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient

class AzureService:
    def __init__(self):
        # Azure CLU Settings
        self.azureKeyCredential = AzureKeyCredential(os.getenv("AZURE_CLU_API_KEY"))
        self.azureEndpoint = os.getenv("AZURE_CLU_ENDPOINT")
        self.azureProjectName = os.getenv("AZURE_CLU_PROJECT_NAME")
        self.azureDeploymentName = os.getenv("AZURE_CLU_DEPLOYMENT_NAME")

    def analyze_address(self, address):
        client = ConversationAnalysisClient(self.azureEndpoint, self.azureKeyCredential)
        with client:
            result = client.analyze_conversation(
                task={
                    "kind": "Conversation",
                    "analysisInput": {
                        "conversationItem": {
                            "participantId": "1",
                            "id": "1",
                            "modality": "text",
                            "language": "zh-hant",
                            "text": address
                        },
                        "isLoggingEnabled": False
                    },
                    "parameters": {
                        "projectName": self.azureProjectName,
                        "deploymentName": self.azureDeploymentName,
                        "verbose": True
                    }
                }
            )
        return result['result']
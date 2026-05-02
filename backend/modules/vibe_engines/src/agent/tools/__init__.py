# Dummy BaseTool to satisfy imports for Vibe-Trading tools

class BaseTool:
    name = "base_tool"
    description = "Dummy base tool"
    parameters = {}
    
    def execute(self, **kwargs) -> str:
        return ""

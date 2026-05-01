from fastapi import FastAPI


def setup_event_handlers(app: FastAPI) -> None:
    @app.on_event("startup")
    async def startup() -> None:
        pass

    @app.on_event("shutdown")
    async def shutdown() -> None:
        pass

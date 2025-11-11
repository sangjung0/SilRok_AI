from dependency_injector.containers import DeclarativeContainer


class ContainerManager:
    def __init__(self, container: DeclarativeContainer) -> None:
        self.container: DeclarativeContainer = container

    async def start(self) -> None:
        await self.container.init_resources()

    async def stop(self) -> None:
        # self.unregister_socket_handlers()
        await self.container.shutdown_resources()


__all__ = ["ContainerManager"]

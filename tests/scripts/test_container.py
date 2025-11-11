from dependency_injector import containers, providers, resources
import asyncio


class MyAsyncResource(resources.AsyncResource):
    def __init__(self):
        super().__init__()
        print("🔧 MyAsyncResource initialized")

    async def init(self, a) -> str:
        print("🔧 async init called")
        return self

    async def shutdown(self, resource):
        print(resource)
        return await super().shutdown(resource)

    def pt(self):
        print("test")


class MyContainer(containers.DeclarativeContainer):
    my_resource = providers.Resource(MyAsyncResource, a = 1)


# 실행 예
async def main():
    container = MyContainer()
    await container.init_resources()  # 🔧 호출됨
    instance = await container.my_resource()  # 반환값 사용 가능
    instance.pt()
    instance = await container.my_resource()  # 반환값 사용 가능
    instance.pt()
    print("✅ got:", instance)
    await container.shutdown_resources()  # 🧹 호출됨


asyncio.run(main())

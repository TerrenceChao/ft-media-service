from pydantic import BaseModel
from ..infra.resources.handlers.storage_resource import *
from ..infra.resources.manager import resource_manager

storage_resource: S3ResourceHandler = resource_manager.get('storage_resource')
storage_client: S3ResourceClientHandler = resource_manager.get('storage_client')




class StorageAdapter(BaseModel):
    resource: S3ResourceHandler
    client: S3ResourceClientHandler

    # Pydantic 默認不允許自定義類型
    # 當 arbitrary_types_allowed 設置為 True 時，允許任意類型的字段
    class Config:
        arbitrary_types_allowed = True

storage_adapter = StorageAdapter(
    resource=storage_resource,
    client=storage_client,
)

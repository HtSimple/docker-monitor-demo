import docker
import os
import time
from typing import Optional, Dict, List

class DockerTrainManager:
    def __init__(self):
        self.client = docker.from_env()
        self.train_image_name = "train-task:latest"
        self.monitor_network = "docker-monitor-demo_monitor-network"

    def build_train_image(self, dockerfile_path: str = "./") -> bool:
        try:
            print(f"开始构建镜像 {self.train_image_name}...")
            self.client.images.build(
                path=dockerfile_path,
                tag=self.train_image_name,
                rm=True
            )
            print(f"镜像 {self.train_image_name} 构建成功")
            return True
        except Exception as e:
            print(f"镜像构建失败：{str(e)}")
            return False

    def create_train_container(
        self,
        task_id: str,
        resource_limits: Optional[Dict] = None,
        gpu_support: bool = False
    ) -> str:
        container_name = f"train-task-{task_id}"
        if self.check_container_exists(container_name):
            print(f"容器 {container_name} 已存在，先销毁")
            self.stop_and_remove_container(container_name)

        limits = resource_limits or {"cpus": "2.0", "mem_limit": "8g"}
        container_kwargs = {
            "name": container_name,
            "image": self.train_image_name,
            "command": [task_id],
            "detach": True,
            "network": self.monitor_network,
            "auto_remove": True,
            "cpu_shares": 1024,** limits
        }

        if gpu_support:
            container_kwargs["device_requests"] = [
                docker.types.DeviceRequest(
                    count=-1,
                    capabilities=[["gpu"]]
                )
            ]

        try:
            container = self.client.containers.run(**container_kwargs)
            print(f"容器 {container_name} (ID: {container.id[:8]}) 启动成功")
            return container.id
        except Exception as e:
            print(f"容器创建失败：{str(e)}")
            raise

    def check_container_exists(self, container_name: str) -> bool:
        try:
            self.client.containers.get(container_name)
            return True
        except docker.errors.NotFound:
            return False

    def get_container_logs(self, container_name: str, follow: bool = False) -> None:
        try:
            container = self.client.containers.get(container_name)
            print(f"===== 容器 {container_name} 日志 =====")
            if follow:
                for log in container.logs(stream=True, follow=True):
                    print(log.decode("utf-8").strip())
            else:
                logs = container.logs().decode("utf-8")
                print(logs)
        except Exception as e:
            print(f"获取日志失败：{str(e)}")

    def stop_and_remove_container(self, container_name: str) -> bool:
        try:
            container = self.client.containers.get(container_name)
            if container.status == "running":
                container.stop()
                print(f"容器 {container_name} 已停止")
            container.remove(force=True)
            print(f"容器 {container_name} 已删除")
            return True
        except docker.errors.NotFound:
            print(f"容器 {container_name} 不存在")
            return True
        except Exception as e:
            print(f"容器销毁失败：{str(e)}")
            return False

    def wait_container_complete(self, container_name: str, poll_interval: int = 5) -> bool:
        try:
            while True:
                container = self.client.containers.get(container_name)
                if container.status != "running":
                    print(f"容器 {container_name} 运行完成，状态：{container.status}")
                    return True
                print(f"容器 {container_name} 仍在运行中...")
                time.sleep(poll_interval)
        except Exception as e:
            print(f"等待容器完成失败：{str(e)}")
            return False

    def list_train_containers(self) -> List[Dict]:
        containers = []
        for container in self.client.containers.list(all=True):
            if container.name.startswith("train-task-"):
                containers.append({
                    "name": container.name,
                    "id": container.id[:8],
                    "status": container.status,
                    "image": container.image.tags[0],
                    "created": container.attrs["Created"]
                })
        return containers

    def cleanup_old_containers(self, hours: int = 1) -> None:
        print(f"清理 {hours} 小时前创建的训练容器...")
        cutoff_time = time.time() - (hours * 3600)
        for container in self.client.containers.list(all=True):
            if container.name.startswith("train-task-"):
                created_time = container.attrs["Created"].split("T")[0]
                created_ts = time.mktime(time.strptime(created_time, "%Y-%m-%d"))
                if created_ts < cutoff_time:
                    self.stop_and_remove_container(container.name)

if __name__ == "__main__":
    manager = DockerTrainManager()
    manager.build_train_image()
    print("当前训练容器：", manager.list_train_containers())
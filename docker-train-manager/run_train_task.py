from docker_manager import DockerTrainManager
from export_metrics import export_task_metrics
import argparse
import time

def run_single_train_task(task_id: str, use_gpu: bool = False):
    manager = DockerTrainManager()
    if not manager.build_train_image():
        exit(1)

    container_name = f"train-task-{task_id}"
    try:
        # 修复：将 cpus 替换为旧版兼容的 cpu_quota/cpu_period 参数
        # 2.0 核对应 cpu_quota=200000，cpu_period=100000（1核=100000）
        resource_limits = {
            "cpu_quota": 200000,    # 替代 cpus: 2.0
            "cpu_period": 100000,
            "mem_limit": "8g"
        }
        manager.create_train_container(
            task_id=task_id,
            resource_limits=resource_limits,  # 传入修正后的资源限制
            gpu_support=use_gpu
        )
    except Exception as e:
        print(f"启动容器失败：{str(e)}")
        exit(1)

    print("开始跟踪训练日志...")
    manager.get_container_logs(container_name, follow=True)
    manager.wait_container_complete(container_name)

    print("开始导出监控指标...")
    export_task_metrics(task_id=task_id, container_name=container_name)
    manager.cleanup_old_containers(hours=1)
    print(f"任务 {task_id} 全流程完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行Docker训练任务")
    parser.add_argument("--task-id", required=True, help="唯一任务ID")
    parser.add_argument("--use-gpu", action="store_true", help="是否启用GPU")
    args = parser.parse_args()
    run_single_train_task(task_id=args.task_id, use_gpu=args.use_gpu)
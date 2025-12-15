import requests
import json
import time
import os

PROMETHEUS_URL = "http://localhost:9090"
EXPORT_DIR = "./metrics_export"

def calculate_metric_summary(values, metric_type):
    """
    计算指标汇总值
    :param values: 原始值列表 [[时间戳, 值], ...]
    :param metric_type: 指标类型 (cpu/mem/disk/network)
    :return: 汇总结果
    """
    if not values or len(values) < 2:
        return 0.0 if metric_type != "mem" else {"peak_mb": 0.0, "avg_mb": 0.0}
    
    # 提取数值并转换为浮点数
    nums = [float(v[1]) for v in values]
    
    if metric_type == "cpu":
        # CPU：总消耗 = 最终值 - 初始值
        return round(float(values[-1][1]) - float(values[0][1]), 4)
    elif metric_type == "mem":
        # 内存：峰值 + 平均值（转MB）
        peak = max(nums) / 1024 / 1024
        avg = sum(nums) / len(nums) / 1024 / 1024
        return {"peak_mb": round(peak, 2), "avg_mb": round(avg, 2)}
    elif metric_type in ["disk", "network_rx", "network_tx"]:
        # 磁盘/网络：总使用量（转MB）
        total = (float(values[-1][1]) - float(values[0][1])) if metric_type.startswith("network") else float(values[-1][1])
        return round(total / 1024 / 1024, 4)
    return 0.0

def export_task_metrics(
    task_id: str,
    container_name: str,
    time_range_hours: int = 1
) -> bool:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    end_ts = int(time.time())
    start_ts = end_ts - (time_range_hours * 3600)

    # 定义要查询的指标
    metrics = {
        "cpu": "container_cpu_usage_seconds_total{name='%s'}" % container_name,
        "mem": "container_memory_usage_bytes{name='%s'}" % container_name,
        "disk": "container_fs_usage_bytes{name='%s'}" % container_name,
        "network_rx": "container_network_receive_bytes_total{name='%s'}" % container_name,
        "network_tx": "container_network_transmit_bytes_total{name='%s'}" % container_name
    }

    # 最终汇总结果（极简结构）
    summary_result = {
        "task_info": {
            "task_id": task_id,
            "container_name": container_name,
            "time_range": f"{time_range_hours}小时",
            "query_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        },
        "metrics_summary": {}
    }

    for metric_type, query in metrics.items():
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={"query": query, "start": start_ts, "end": end_ts, "step": 10},
                timeout=30
            )
            response.raise_for_status()
            resp_json = response.json()

            if resp_json["status"] == "success" and resp_json["data"]["result"]:
                if metric_type == "cpu":
                    # CPU：汇总所有核心/容器实例的总消耗
                    total_cpu = 0.0
                    for result in resp_json["data"]["result"]:
                        cpu_consume = calculate_metric_summary(result["values"], "cpu")
                        total_cpu += cpu_consume
                    summary_result["metrics_summary"]["cpu_total_core_seconds"] = total_cpu
                    summary_result["metrics_summary"]["cpu_summary"] = (
                        f"总CPU消耗：{total_cpu:.4f}核心秒（等价1核CPU运行{total_cpu:.2f}秒）"
                    )
                elif metric_type == "mem":
                    # 内存：取第一个容器实例的峰值/平均值（默认最新实例）
                    mem_summary = calculate_metric_summary(resp_json["data"]["result"][0]["values"], "mem")
                    summary_result["metrics_summary"]["memory_peak_mb"] = mem_summary["peak_mb"]
                    summary_result["metrics_summary"]["memory_avg_mb"] = mem_summary["avg_mb"]
                else:
                    # 磁盘/网络：取第一个容器实例的汇总值
                    total_val = calculate_metric_summary(resp_json["data"]["result"][0]["values"], metric_type)
                    if metric_type == "disk":
                        summary_result["metrics_summary"]["disk_usage_mb"] = total_val
                    elif metric_type == "network_rx":
                        summary_result["metrics_summary"]["network_rx_total_mb"] = total_val
                    elif metric_type == "network_tx":
                        summary_result["metrics_summary"]["network_tx_total_mb"] = total_val

            print(f"✅ 指标 {metric_type} 汇总成功")
        except Exception as e:
            error_msg = f"❌ 指标 {metric_type} 汇总失败：{str(e)}"
            print(error_msg)
            summary_result["metrics_summary"][f"{metric_type}_error"] = error_msg

    # 保存极简汇总结果
    export_file = os.path.join(EXPORT_DIR, f"train_task_{task_id}_summary.json")
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(summary_result, f, indent=4, ensure_ascii=False)

    print(f"\n📊 极简汇总结果已导出至：{export_file}")
    # 打印核心结果（控制台快速查看）
    print("\n========== 核心指标汇总 ==========")
    for k, v in summary_result["metrics_summary"].items():
        print(f"{k}: {v}")
    return True

if __name__ == "__main__":
    export_task_metrics(
        task_id="test-001",
        container_name="train-task-test-001",
        time_range_hours=1
    )
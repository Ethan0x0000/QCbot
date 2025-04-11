import json
import os
from datetime import datetime
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / "storage" / "sign" / "data.json"

class SignSystem:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self):
        if not DATA_PATH.exists():
            return {"users": {}}
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _calculate_rank(self):
        users = sorted(
            self.data["users"].values(),
            key=lambda x: x["points"],
            reverse=True
        )
        for rank, user in enumerate(users, 1):
            user["rank"] = rank

    def sign(self, wxid):
        today = datetime.now().strftime("%Y-%m-%d")
        user = self.data["users"].get(wxid, {
            "last_sign_date": None,
            "continuous_days": 0,
            "points": 0,
            "rank": 0
        })

        # 检查是否已签到
        if user["last_sign_date"] == today:
            return {
                "success": False,
                "already_signed": True,
                "continuous_days": user["continuous_days"],
                "points": user["points"],
                "rank": user["rank"]
            }

        # 计算连续签到天数
        last_date = datetime.strptime(user["last_sign_date"], "%Y-%m-%d") if user["last_sign_date"] else None
        today_date = datetime.strptime(today, "%Y-%m-%d")
        if last_date and (today_date - last_date).days == 1:
            user["continuous_days"] += 1
        else:
            user["continuous_days"] = 1

        # 计算积分
        base_points = 10
        extra_points = min(user["continuous_days"] - 1, 10)
        user["points"] += base_points + extra_points
        user["last_sign_date"] = today

        # 更新用户数据
        self.data["users"][wxid] = user
        self._calculate_rank()
        self._save_data()

        return {
            "success": True,
            "already_signed": False,
            "continuous_days": user["continuous_days"],
            "points": user["points"],
            "rank": user["rank"]
        }

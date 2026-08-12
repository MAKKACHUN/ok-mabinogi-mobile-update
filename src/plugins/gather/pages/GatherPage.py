from typing import Any


class GatherPage:
    """
    採集資源頁面。

    職責：
    1. 在右側資源列表搜尋指定資源
    2. 找不到時滾動列表
    3. 點擊指定資源
    4. 點擊「尋找附近位置」
    """

    FIND_NEARBY_FEATURE = "find_nearby_location"

    # 「尋找附近位置」會因不同資源詳情內容高度而上下移動。
    #
    # 1600x900 畫面：
    # horizontal_variance=0.05 -> 左右約 ±80px
    # vertical_variance=0.20   -> 上下約 ±180px
    FIND_NEARBY_HORIZONTAL_VARIANCE = 0.05
    FIND_NEARBY_VERTICAL_VARIANCE = 0.20

    FIND_NEARBY_THRESHOLD = 0.8

    def __init__(
        self,
        task: Any,
    ) -> None:
        """
        Args:
            task:
                AutoGatherTask 實例。

                Page Object 會使用 Task 已有的：
                - find_resource()
                - move_and_click_box()
                - wait_until()
                - find_one()
                - log_info()
        """

        self.task = task

    def select_resource(
        self,
        resource_name: str,
        resource_feature: str,
        competing_resource_features: tuple[str, ...] = (),
        after_sleep: float = 1.0,
    ) -> None:
        """
        搜尋並點擊指定資源。

        Args:
            resource_name:
                顯示於 log 的資源名稱，例如「銅礦脈」。

            resource_feature:
                Template 名稱，例如「copper_ore_item」。

            after_sleep:
                點擊後等待時間。
        """

        self.task.log_info(
            f"尋找資源：「{resource_name}」"
        )

        resource_box = self.task.find_resource(
            feature_name=resource_feature,
            competing_feature_names=competing_resource_features,
        )

        if resource_box is None:
            raise RuntimeError(
                f"滾動列表後仍然找不到資源："
                f"{resource_name} "
                f"({resource_feature})"
            )

        self.task.log_info(
            f"點擊資源：「{resource_name}」"
        )

        self.task.move_and_click_box(
            resource_box,
            after_sleep=after_sleep,
        )

    def find_nearby(
        self,
        timeout: float,
        after_sleep: float = 2.0,
    ) -> None:
        """
        搜尋並點擊「尋找附近位置」。

        不使用全域預設的極小搜尋偏移。

        因為不同採集物的詳情內容高度不同，
        「尋找附近位置」的 Y 座標會上下移動。

        本方法只針對 find_nearby_location
        放寬搜尋範圍，不會影響其他 Template。
        """

        self.task.log_info(
            "等待並搜尋「尋找附近位置」"
        )

        self.task.log_info(
            "「尋找附近位置」搜尋範圍："
            f"horizontal_variance="
            f"{self.FIND_NEARBY_HORIZONTAL_VARIANCE}，"
            f"vertical_variance="
            f"{self.FIND_NEARBY_VERTICAL_VARIANCE}"
        )

        find_nearby_box = self.task.wait_until(
            lambda: self.task.find_one(
                feature_name=self.FIND_NEARBY_FEATURE,

                # 重點：
                # 覆蓋 config.py 的全域 0.004
                horizontal_variance=(
                    self.FIND_NEARBY_HORIZONTAL_VARIANCE
                ),
                vertical_variance=(
                    self.FIND_NEARBY_VERTICAL_VARIANCE
                ),

                threshold=(
                    self.FIND_NEARBY_THRESHOLD
                ),
            ),
            time_out=timeout,
            raise_if_not_found=False,
        )

        if find_nearby_box is None:
            raise RuntimeError(
                "等待逾時，找不到圖片素材："
                f"{self.FIND_NEARBY_FEATURE}"
            )

        center_x = int(
            find_nearby_box.x
            + find_nearby_box.width / 2
        )

        center_y = int(
            find_nearby_box.y
            + find_nearby_box.height / 2
        )

        self.task.log_info(
            f"已找到「尋找附近位置」："
            f"x={find_nearby_box.x}, "
            f"y={find_nearby_box.y}, "
            f"width={find_nearby_box.width}, "
            f"height={find_nearby_box.height}, "
            f"center=({center_x}, {center_y}), "
            f"confidence={find_nearby_box.confidence}"
        )

        self.task.move_and_click_box(
            find_nearby_box,
            after_sleep=after_sleep,
        )

        self.task.log_info(
            "已點擊「尋找附近位置」，"
            "角色開始自動尋路及採集"
        )

from typing import Union, List, Optional

import importlib
import pkgutil
import fnmatch
from types import ModuleType

from ..logger.configs import loggers


run_logger = loggers.get_logger("run")


class AutoImportModules:
    """
    递归导入指定包及其所有子包中的模块，支持通过 include/exclude 模式过滤模块全名。
    """

    def __init__(
        self,
        root: str,
        include: Optional[Union[str, List[str]]] = None,
        exclude: Optional[Union[str, List[str]]] = None,
    ):
        """
        Args:
            root: 要搜索的根包名。
            include: 可选，单个字符串或字符串列表，表示包含的模式（fnmatch 通配符）。
                     如果提供，模块的完整名称必须至少匹配其中一个模式才会被导入。
                     若不提供，则不会基于包含规则过滤。
            exclude: 可选，单个字符串或字符串列表，表示排除的模式（fnmatch 通配符）。
                     如果提供，模块的完整名称不能匹配任何模式才会被导入。
                     若不提供，则不会基于排除规则过滤。

        Notes:
            - 模块的完整名称格式为：{包名}.{子包名...}.{模块名}（例如 "myapp.core.tasks"）。
            - 如果不指定任何过滤条件，则会导入所有找到的模块（即所有非包的 .py 文件以及包本身）。
            - 常用示例：include="*.tasks" 可导入所有名为 tasks 的模块（包括 tasks 包及其内部模块）。

        Raises:
            ImportError: 如果根包无法导入。
            TypeError: 如果根包名对应的模块不是包（无 __path__ 属性）。
        """
        self.root = root
        self.include_patterns = self._normalize_patterns(include)
        self.exclude_patterns = self._normalize_patterns(exclude)

        run_logger.info(f"Auto importing modules from package: {self.root}")

        # 尝试导入根包
        try:
            package = importlib.import_module(self.root)
        except ModuleNotFoundError as e:
            run_logger.error(f"无法导入根包 {self.root}: {e}")
            raise ImportError(f"根包 '{self.root}' 未找到") from e

        # 检查是否为包（含有 __path__）
        if not hasattr(package, "__path__"):
            run_logger.error(f"'{self.root}' 不是包，无法递归查找模块")
            raise TypeError(f"'{self.root}' 不是包，请提供一个包名")

        # 开始递归导入
        self._find_and_import(self.root, package)

    @staticmethod
    def _normalize_patterns(patterns: Optional[Union[str, List[str]]]) -> List[str]:
        """将输入的模式参数规范化为列表，None 转换为空列表"""
        if patterns is None:
            return []
        if isinstance(patterns, str):
            return [patterns]
        # 假设是列表，但未检查元素类型，留待 fnmatch 处理异常
        return patterns

    def _matches_filters(self, module_full_name: str) -> bool:
        """检查模块全名是否匹配 include/exclude 规则"""
        # include 规则：如果指定了 include，则至少匹配一个模式
        if self.include_patterns:
            if not any(fnmatch.fnmatch(module_full_name, pat) for pat in self.include_patterns):
                return False
        # exclude 规则：不能匹配任何 exclude 模式
        if self.exclude_patterns:
            if any(fnmatch.fnmatch(module_full_name, pat) for pat in self.exclude_patterns):
                return False
        return True

    def _find_and_import(self, cur_root: str, cur_package: ModuleType) -> None:
        """递归遍历包及其子包，导入符合条件的模块（包括子包本身）"""
        for _, mod_name, is_pkg in pkgutil.iter_modules(cur_package.__path__):
            full_name = f"{cur_root}.{mod_name}"

            # 先检查过滤条件，决定是否处理该模块/包
            if not self._matches_filters(full_name):
                run_logger.debug(f"模块/包 {full_name} 被过滤跳过")
                continue  # 跳过这个模块/包及其子内容（如果是包则跳过整个子树）

            # 如果是模块文件（非包），直接导入
            if not is_pkg:
                try:
                    importlib.import_module(full_name)
                    run_logger.info(f"已导入模块: {full_name}")
                except Exception as e:
                    run_logger.exception(f"导入模块失败: {full_name} - {e}")
            else:  # 是子包
                try:
                    sub_package = importlib.import_module(full_name)
                    # 递归遍历子包
                    self._find_and_import(full_name, sub_package)
                except Exception as e:
                    run_logger.exception(f"导入子包失败: {full_name}，跳过其内部模块 - {e}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import Optional

SQL = """
SELECT * FROM test_1 t1, test_2 t2 WHERE t1.colA = t2.colA AND t1.colB = t2.colC;
"""
TREE_INPUT = """
2 3
i 1
i 2
i 3
d 2
i 2
d 3
"""
TREE_SUFFIX = """
g my-tree.dot
q
"""
TERRIER_OUT_FILE = "terrier-bench.txt"


def cmd_viz_repl():
    """
    VSCode B+Tree REPL: 支持size的初始化和命令i、d、q
    强烈建议在VSCode终端使用(注意每次交互会移动光标)
    需要环境有软件graphviz(即命令dot)
    本质就是记录输入, 换行时拼接调用
    """

    def run_cmd(cmd: str):
        DryadUtil.run_shell_cmd(
            cmd, pre_cmd=["cd build"], is_print_cmd_and_result_code=False
        )

    # compile
    run_cmd("make b_plus_tree_printer -j$(nproc)")

    print(cmd_viz_repl.__doc__)

    init_input = input("init: ")
    # check and config init input
    pattern = re.compile(r"^\d+\s+\d+$")  # 匹配一行两个空格隔开的整数的正则表达式
    if pattern.match(init_input) is None:
        print(f'初始语句"{init_input}"不合法, 请使用空格隔开的两个整数')
        exit(-1)
    init_input += "\n"

    # constant
    DOT_FILE_NAME = "my-tree.dot"
    SUFFIX_INPUT = f"\ng {DOT_FILE_NAME}\nq\n"

    input_sum = ""
    while True:
        line = input()
        if line.strip() == "q":
            break
        try:
            action, key = line.strip().split()
        except Exception as e:
            print("[\033[31mInvalid Args\033[0m] Do not process, continue inputting.")
            continue
        if action not in ("i", "d") or key.isdigit() is False:
            print("[\033[31mInvalid Args\033[0m] Do not process, continue inputting.")
            continue

        # gen dot file
        run_cmd(
            f'echo "{init_input + input_sum + line + SUFFIX_INPUT}" | ./bin/b_plus_tree_printer > /dev/null'
        )

        # check dot file
        if os.path.exists(os.path.join("build", DOT_FILE_NAME)) is False:
            print("[\033[31mError Exe\033[0m] 官方脚本未生成dot文件, 猜测图为空, 该输入回退, 继续输入.")
            continue
        # accept input
        input_sum += line

        # viz
        run_cmd(f"dot -Tpng -O {DOT_FILE_NAME}")
        run_cmd(f"code {DOT_FILE_NAME}.png")

        # sufix handle
        run_cmd(f"rm {DOT_FILE_NAME}")


def debug_terrier_helper():
    """final_helper
    处理命令生成的脚本
    主要是对特定格式进行解析然后按6.824的方式输出
    需要CPP端的配合, 已在梗犬测试代码(terrier_debug.cpp)中修改
    """
    from rich import print as rich_print
    from rich.columns import Columns
    from rich.console import Console

    width = Console().size.width
    COL_NUM = 5

    def pick(line: str) -> (Optional[str], Optional[str]):
        PATTERN = r"T(\d): (.*)"

        match = re.match(PATTERN, line)
        if match is not None:
            index = int(match.group(1)) - 1
            msg = match.group(2)
            return (index, msg)
        else:
            return (None, None)

    else_msg = ""

    cols = ["Thread" + str(i) for i in range(5)]
    col_width = int(width / COL_NUM)
    cols = Columns(cols, width=col_width - 1, equal=True, expand=True)
    rich_print(cols)

    with open(f"build/{TERRIER_OUT_FILE}", "r") as f:
        for line in f:
            i, msg = pick(line)
            if i is None:
                assert msg is None, "Logic Error"
                else_msg += line
                continue
            cols = ["" for _ in range(COL_NUM)]
            cols[i] = msg
            col_width = int(width / COL_NUM)
            cols = Columns(cols, width=col_width - 1, equal=True, expand=True)
            rich_print(cols)

    # print(else_msg)


CMDS = {
    "viz": [
        "make b_plus_tree_printer -j$(nproc)",
        f'echo "{TREE_INPUT + TREE_SUFFIX}" | ./bin/b_plus_tree_printer',
        "dot -Tpng -O my-tree.dot",
        "code my-tree.dot.png",
    ],
    "viz-repl": cmd_viz_repl,
    "format": {
        "default": ["make format", "make check-lint"],
        "1": ["make check-clang-tidy-p1"],
        "2": ["make check-clang-tidy-p2"],
        "3": ["make check-clang-tidy-p3"],
        "4": ["make check-clang-tidy-p4"],
    },
    "test": {
        "1": {
            "1": [
                "make lru_k_replacer_test -j$(nproc)",
                "./test/lru_k_replacer_test",
            ],
            "2": [
                "make buffer_pool_manager_test -j$(nproc)",
                "./test/buffer_pool_manager_test",
            ],
            "3": [
                "make page_guard_test -j$(nproc)",
                "./test/page_guard_test",
            ],
        },
        "2": {
            # 按照Task视角
            # Check Point 1
            "1": ['echo "Pages Structure."'],
            "2a": ['echo "Insert and Search."'],
            # Check Point 2
            "2b": ['echo "Delete."'],
            "3": ['echo "Interator"'],
            "4": ['echo "Concurrency"'],
            # 按照Check Pointer视角
            "cp1": [
                "make b_plus_tree_insert_test -j$(nproc)",
                "./test/b_plus_tree_insert_test",
                "make b_plus_tree_sequential_scale_test -j$(nproc)",
                "./test/b_plus_tree_sequential_scale_test",
            ],
            "cp2": [
                "make b_plus_tree_insert_test -j$(nproc)",
                "./test/b_plus_tree_insert_test",
                "make b_plus_tree_delete_test -j$(nproc)",
                "./test/b_plus_tree_delete_test",
                "make b_plus_tree_sequential_scale_test -j$(nproc)",
                "./test/b_plus_tree_sequential_scale_test",
                "make b_plus_tree_concurrent_test -j$(nproc)",
                "./test/b_plus_tree_concurrent_test",
            ],
            # 按照开发流程视角
            "main": ['echo "Main."'],
        },
        "3": [
            "make -j$(nproc) sqllogictest",
            'echo "Task 1"',
            "./bin/bustub-sqllogictest ../test/sql/p3.00-primer.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.01-seqscan.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.02-insert.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.04-delete.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.03-update.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.05-index-scan.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.06-empty-table.slt --verbose",
            'echo "Aggregation"',
            "./bin/bustub-sqllogictest ../test/sql/p3.07-simple-agg.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.08-group-agg-1.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.09-group-agg-2.slt --verbose",
            'echo "NestedLoopJoin"',
            "./bin/bustub-sqllogictest ../test/sql/p3.10-simple-join.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.11-multi-way-join.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.12-repeat-execute.slt --verbose",
            'echo "NestedIndexJoin(实际无效, GradeScope也未测试, Planer并未生成NestedIndexJoin结点, sqllogictest相关的检测终止了进程)"',
            # "./bin/bustub-sqllogictest ../test/sql/p3.13-nested-index-join.slt --verbose",
            'echo "HashJoin"',
            "./bin/bustub-sqllogictest ../test/sql/p3.14-hash-join.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.15-multi-way-hash-join.slt --verbose",
            'echo "Task 3"',
            "./bin/bustub-sqllogictest ../test/sql/p3.16-sort-limit.slt --verbose",
            "./bin/bustub-sqllogictest ../test/sql/p3.17-topn.slt --verbose",
            # "./bin/bustub-sqllogictest ../test/sql/p3.18-integration-1.slt --verbose",
            # "./bin/bustub-sqllogictest ../test/sql/p3.19-integration-2.slt --verbose",
            'echo "leaderboard"',
            # "./bin/bustub-sqllogictest ../test/sql/p3.leaderboard-q1.slt --verbose",
            # "./bin/bustub-sqllogictest ../test/sql/p3.leaderboard-q2.slt --verbose",
            # "./bin/bustub-sqllogictest ../test/sql/p3.leaderboard-q3.slt --verbose",
        ],
        "4": {
            "1": [
                "make lock_manager_test -j`nproc`",
                "./test/lock_manager_test",
            ],
            "2": [
                "make deadlock_detection_test -j`nproc`",
                "./test/deadlock_detection_test",
                "make wuxiao_deadlock_detection_test -j`nproc`",
                "./test/wuxiao_deadlock_detection_test",
            ],
            "3": [
                "make zweix_lock_manager_test -j`nproc`",
                "./test/zweix_lock_manager_test ",
                "make txn_integration_test -j`nproc`",
                "./test/txn_integration_test ",
                "make wuxiao_lock_manager_test -j`nproc`",
                "./test/wuxiao_lock_manager_test",
                "make wuxiao_lock_manager_compability_test -j`nproc`",
                "./test/wuxiao_lock_manager_compability_test",
                "make wuxiao_lock_manager_isolation_test -j`nproc`",
                "./test/wuxiao_lock_manager_isolation_test",
            ],
        },
    },
    "submit": {
        "1": ["make submit-p1"],
        "2": ["make submit-p2"],
        "3": ["make submit-p3"],
        "4": ["make submit-p4"],
    },
    "run": [
        "make -j`nproc` shell",
        "./bin/bustub-shell",
    ],
    "test-SQL": [
        "make -j`nproc` shell",
        f'echo "{SQL}" | ./bin/bustub-shell 2> /dev/null',
    ],
    "test-terrier": [
        "make -j`nproc` terrier-bench",
        "./bin/bustub-terrier-bench --duration 30000",
    ],
    "terrier-debug": [
        "make -j`nproc` terrier-debug",
        f"./bin/bustub-terrier-debug --duration 30000 > {TERRIER_OUT_FILE} 2>&1 || true",
        debug_terrier_helper,
    ],
}

# ================================================================= #


import os
import subprocess
import sys
from typing import Any, Callable


class DryadConfig:
    SCRIPTPATH = os.path.dirname(os.path.abspath(__file__))
    CALLPATH = os.getcwd()
    OSTYPE = sys.platform


class DryadUtil:
    @staticmethod
    def config():
        if DryadConfig.OSTYPE == "win32":
            pass
        elif DryadConfig.OSTYPE == "linux":
            pass
        elif DryadConfig.OSTYPE == "darwin":
            pass
        else:
            assert False

    @staticmethod
    def run_shell_cmd(
        cmd: str,
        pre_cmd: list[str] = [],
        is_print_cmd_and_result_code: bool = True,
    ) -> None:
        assert type(cmd) is str
        if is_print_cmd_and_result_code:
            print("\033[33;1m" + cmd + "\033[0m")
        cmd = "\n".join(pre_cmd) + "\n" + cmd
        try:
            if DryadConfig.OSTYPE == "win32":
                assert False, "Not Impl"
            elif DryadConfig.OSTYPE == "linux":
                subprocess.run(["bash", "-c", cmd], check=True)
            else:
                assert False, "Not Impl"
        except Exception as e:
            if is_print_cmd_and_result_code:
                print("\033[41m\033[37m" + "Fail" + "\033[0m")
            exit(-1)
        # if is_print_cmd_and_result_code:
        #     print("\033[42m\033[37m" + "Pass" + "\033[0m")

    @staticmethod
    def right_shift(text: str | list[str], dis: int) -> str:
        if type(text) is str:
            text = [text]
        SPACE_LEN = max([len(line) for line in text]) + 42
        ss = [
            s if len(s) != 0 else " " * SPACE_LEN
            for l in [map(str.strip, line.split("\n")) for line in text]
            for s in l
        ]
        assert max([len(s) for s in ss]) <= SPACE_LEN
        while not any(len(s) == 0 or s[0] != " " for s in ss):
            ss = [s[1:] for s in ss]
        return ("\n" + " " * dis).join(map(str.strip, ss)).strip()


class Dryad:
    def __init__(self, cmd_tree: dict, cmd_prefix: list[str] = []) -> None:
        self.cmd_tree = cmd_tree
        self.cmd_prefix = cmd_prefix

        self.config()
        self.main()

    def config(self):
        self.cmd_tree[("-h", "--help")] = self.print_help

        if DryadConfig.OSTYPE == "win32":
            assert False, f"{DryadConfig.OSTYPE} not yet tested, can't be used."
        elif DryadConfig.OSTYPE == "linux":
            self.cmd_prefix = ["set -e"] + self.cmd_prefix
        else:
            assert False, f"{DryadConfig.OSTYPE} not yet tested, can't be used."

        DryadUtil.config()

    def main(self):
        self.options = sys.argv[1:]
        if len(self.options) == 0:
            self.print_help()
        else:
            self.opt_dfs(self.options, self.cmd_tree)

    def print_help(self):
        """Print commands and desciptions supported by script.py."""
        print("该脚本命令可分为两大类")
        print("  Shell Commands, help会输出命令本身")
        print("  Python Function, help会输出函数的__doc__")
        print("命令是支持前缀递归调用的, 比如./script.py test相当于调用所有以test为前缀的命令.")

        def dfs_handle_cmds_doc(cmds: dict | list | str | Callable):
            """递归处理命令树中命令的内容和文档"""
            assert (
                type(dict) is not dict
            ), "Just for mypy, should not be passed into dict"
            if type(cmds) is str:
                return cmds.strip("\n")
            elif type(cmds) is list:
                return "\n".join([dfs_handle_cmds_doc(cmd) for cmd in cmds])
            elif callable(cmds):
                return cmds.__doc__.strip("\n") if cmds.__doc__ is not None else "None"
            else:
                assert False

        def dfs_handle_opts(opt: list[str], remain_cmds: dict | Any):
            if type(remain_cmds) is not dict:  # 递归到选项边界
                opts = " ".join(opt)
                doc = DryadUtil.right_shift(
                    dfs_handle_cmds_doc(remain_cmds), len(opts + ": ")
                )
                print(f"\033[36m{opts}\033[0m: \033[33m{doc}\033[0m")
                return
            for k, v in remain_cmds.items():
                if type(k) is tuple:
                    opt.append("/".join(k))
                elif type(k) is str:
                    opt.append(k)
                else:
                    assert False
                dfs_handle_opts(opt, v)
                opt.pop()

        dfs_handle_opts([], self.cmd_tree)

    def dfs_run(self, cmds: dict | list | str | Callable):
        if callable(cmds):
            cmds()
        elif type(cmds) is str:
            DryadUtil.run_shell_cmd(cmds, self.cmd_prefix)
        elif type(cmds) is list:
            for cmd in cmds:
                self.dfs_run(cmd)
        elif type(cmds) is dict:
            for next_cmds in cmds.values():
                self.dfs_run(next_cmds)
        else:
            assert False, "Impossible the type branch: " + "cmds = " + str(cmds)

    def opt_dfs(self, opts: list[str], cmds: dict | list | str | Callable):
        if len(opts) == 0:  # 递归边界
            self.dfs_run(cmds)
            return
        if type(cmds) is not dict or not (
            any(opts[0] == ele for ele in cmds.keys() if type(ele) is not tuple)
            or any(opts[0] in ele for ele in cmds.keys() if type(ele) is tuple)
        ):
            print(f"Don't supported the options: \"{' '.join(self.options)}\"")
            print('Give it a try of option: "--help"')
            return
        # support default
        if len(opts) == 1 and opts[0] != "default" and "default" in cmds.keys():
            #  最后一个选项     这个选项不是default         “子树”命令集中有default
            self.dfs_run(cmds["default"])  # default命令不能使用()做命令重合
        next_cmds = {
            k: v
            for k, v in cmds.items()
            if (type(k) is tuple and opts[0] in k)
            or (type(k) is not tuple and opts[0] == k)
        }
        assert (
            len(next_cmds) == 1
        ), f"歧义参数: opts: {opts}, cmd.kets(): {cmds.keys()}, next_cmds.keys(): {next_cmds.keys()}"
        self.opt_dfs(opts[1:], list(next_cmds.values())[0])


# ================================================================================= #

Dryad(cmd_tree=CMDS, cmd_prefix=["cd build"])

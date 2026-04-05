import sys
import traceback
import networkx as nx

class DynamicAnalyzer:
    """动态分析器，负责追踪运行时调用关系"""
    
    def __init__(self):
        """初始化动态分析器"""
        self.graph = nx.DiGraph()
        self.call_stack = []
    
    def start_tracing(self):
        """
        开始追踪函数调用
        """
        sys.settrace(self._trace_calls)
    
    def stop_tracing(self):
        """
        停止追踪函数调用
        """
        sys.settrace(None)
    
    def _trace_calls(self, frame, event, arg):
        """
        追踪函数调用的回调函数
        
        Args:
            frame: 当前执行帧
            event: 事件类型
            arg: 事件参数
            
        Returns:
            function: 追踪函数
        """
        if event != 'call':
            return
        co = frame.f_code
        func_name = co.co_name
        if func_name == '<module>':
            return
        func_filename = co.co_filename
        caller_frame = frame.f_back
        if caller_frame:
            caller_co = caller_frame.f_code
            caller_func_name = caller_co.co_name
            caller_filename = caller_co.co_filename
            
            # 添加调用关系
            caller = f"{caller_filename}:{caller_func_name}"
            callee = f"{func_filename}:{func_name}"
            self.graph.add_node(caller, type='function', file=caller_filename)
            self.graph.add_node(callee, type='function', file=func_filename)
            self.graph.add_edge(caller, callee, type='calls')
        return self._trace_calls
    
    def get_graph(self):
        """
        获取构建的调用关系图
        
        Returns:
            networkx.DiGraph: 调用关系图
        """
        return self.graph
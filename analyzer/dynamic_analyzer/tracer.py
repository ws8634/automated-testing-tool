"""
动态追踪器，用于追踪运行时的方法调用关系
"""
import sys
import traceback
from typing import List, Dict, Any, Callable, Optional
from collections import defaultdict
import threading
import time


class CallTracer:
    """
    调用追踪器，负责追踪Python代码运行时的函数调用
    """
    
    def __init__(self):
        """
        初始化调用追踪器
        """
        self.traces: List[Dict[str, Any]] = []
        self.call_stack: List[str] = []
        self._original_trace: Optional[Callable] = None
        self._is_tracing = False
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """
        开始追踪
        """
        if self._is_tracing:
            return
        
        self._original_trace = sys.gettrace()
        sys.settrace(self._trace_callback)
        self._is_tracing = True
    
    def stop(self) -> None:
        """
        停止追踪
        """
        if not self._is_tracing:
            return
        
        sys.settrace(self._original_trace)
        self._is_tracing = False
    
    def _trace_callback(self, frame, event, arg):
        """
        追踪回调函数
        
        Args:
            frame: 栈帧
            event: 事件类型
            arg: 参数
        """
        if event == 'call':
            self._handle_call(frame)
        elif event == 'return':
            self._handle_return(frame)
        
        return self._trace_callback
    
    def _handle_call(self, frame) -> None:
        """
        处理函数调用事件
        
        Args:
            frame: 栈帧
        """
        with self._lock:
            func_name = frame.f_code.co_name
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            
            if self._should_trace(filename):
                caller = self.call_stack[-1] if self.call_stack else None
                
                trace_info = {
                    'event': 'call',
                    'function': func_name,
                    'filename': filename,
                    'lineno': lineno,
                    'caller': caller,
                    'timestamp': time.time()
                }
                
                self.traces.append(trace_info)
                self.call_stack.append(func_name)
    
    def _handle_return(self, frame) -> None:
        """
        处理函数返回事件
        
        Args:
            frame: 栈帧
        """
        with self._lock:
            func_name = frame.f_code.co_name
            if self.call_stack and self.call_stack[-1] == func_name:
                self.call_stack.pop()
    
    def _should_trace(self, filename: str) -> bool:
        """
        判断是否应该追踪该文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否应该追踪
        """
        if 'site-packages' in filename or 'lib/python' in filename:
            return False
        return True
    
    def get_call_graph(self) -> Dict[str, Any]:
        """
        获取调用图
        
        Returns:
            调用图字典
        """
        call_edges = defaultdict(list)
        call_counts = defaultdict(int)
        
        for trace in self.traces:
            caller = trace.get('caller')
            callee = trace.get('function')
            
            if caller and callee:
                edge = {'to': callee, 'lineno': trace.get('lineno')}
                if edge not in call_edges[caller]:
                    call_edges[caller].append(edge)
                call_counts[(caller, callee)] += 1
        
        return {
            'edges': dict(call_edges),
            'counts': dict(call_counts),
            'total_calls': len(self.traces)
        }
    
    def clear(self) -> None:
        """
        清空追踪数据
        """
        self.traces.clear()
        self.call_stack.clear()


class DynamicAnalyzer:
    """
    动态分析器，负责执行代码并分析运行时行为
    """
    
    def __init__(self, project_path: str):
        """
        初始化动态分析器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = project_path
        self.tracer = CallTracer()
        self.api_calls: List[Dict[str, Any]] = []
        self.database_queries: List[Dict[str, Any]] = []
    
    def analyze(self, entry_point: str) -> Dict[str, Any]:
        """
        执行动态分析
        
        Args:
            entry_point: 入口点文件路径
            
        Returns:
            分析结果字典
        """
        self.tracer.clear()
        
        try:
            self.tracer.start()
            self._execute_entry_point(entry_point)
        except Exception as e:
            print(f"执行入口点时出错: {e}")
            traceback.print_exc()
        finally:
            self.tracer.stop()
        
        return self._build_result()
    
    def _execute_entry_point(self, entry_point: str) -> None:
        """
        执行入口点
        
        Args:
            entry_point: 入口点文件路径
        """
        import importlib.util
        import sys
        
        abs_path = os.path.join(self.project_path, entry_point)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"入口点文件不存在: {abs_path}")
        
        spec = importlib.util.spec_from_file_location("entry_module", abs_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["entry_module"] = module
            spec.loader.exec_module(module)
    
    def _build_result(self) -> Dict[str, Any]:
        """
        构建分析结果
        
        Returns:
            分析结果字典
        """
        return {
            'call_graph': self.tracer.get_call_graph(),
            'api_calls': self.api_calls,
            'database_queries': self.database_queries,
            'traces': self.tracer.traces
        }


def trace_function(func: Callable) -> Callable:
    """
    装饰器：追踪函数调用
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        tracer = CallTracer()
        tracer.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            tracer.stop()
    
    return wrapper

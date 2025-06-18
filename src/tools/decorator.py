import logging
import functools
import inspect
from typing import Any, Callable, Type, TypeVar
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
T = TypeVar("T")

def log_method_io(method: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to log input and output of a method with detailed parameter information.
    仅包装同步方法。
    """
    @functools.wraps(method)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(method)
        params = sig.parameters
        args_dict = {}
        start_idx = 1 if list(params.keys())[0] == 'self' else 0
        for param_name, arg in zip(list(params.keys())[start_idx:], args[start_idx:]):
            args_dict[param_name] = arg
        all_args = {**args_dict, **kwargs}
        logger.debug(
            f"Calling {method.__name__} with parameters:\n" + 
            "\n".join(f"  {name}: {value}" for name, value in all_args.items())
        )
        result = method(*args, **kwargs)
        logger.debug(f"{method.__name__} returned: {result}")
        return result

    return sync_wrapper


def log_class_io(cls: Type[T]) -> Type[T]:
    """
    Decorator to log input and output of all methods in a class.
    This decorator handles instance methods, class methods, static methods and properties.
    
    :param cls: The class to be decorated.
    :return: The decorated class with logging for all methods.
    """
    logger.debug(f"Applying logging decorator to class: {cls.__name__}")
    
    # 处理所有类成员
    for name, member in inspect.getmembers(cls):
        # 跳过魔术方法
        if name.startswith("__") and name.endswith("__"):
            continue
            
        # 处理属性装饰器
        if isinstance(member, property):
            # 装饰 getter
            if member.fget is not None:
                wrapped_fget = log_method_io(member.fget)
                # 装饰 setter
                wrapped_fset = log_method_io(member.fset) if member.fset is not None else None
                # 装饰 deleter
                wrapped_fdel = log_method_io(member.fdel) if member.fdel is not None else None
                # 创建新的属性
                setattr(cls, name, property(wrapped_fget, wrapped_fset, wrapped_fdel))
                logger.debug(f"Decorated property: {cls.__name__}.{name}")
            continue

        # 处理静态方法
        if isinstance(member, staticmethod):
            original_func = member.__func__
            wrapped_func = log_method_io(original_func)
            setattr(cls, name, staticmethod(wrapped_func))
            logger.debug(f"Decorated static method: {cls.__name__}.{name}")
            continue

        # 处理类方法
        if isinstance(member, classmethod):
            original_func = member.__func__
            wrapped_func = log_method_io(original_func)
            setattr(cls, name, classmethod(wrapped_func))
            logger.debug(f"Decorated class method: {cls.__name__}.{name}")
            continue

        # 处理普通方法
        if inspect.isfunction(member):
            # 不再处理协程，只处理同步方法
            if not inspect.iscoroutinefunction(member):
                setattr(cls, name, log_method_io(member))
                logger.debug(f"Decorated instance method: {cls.__name__}.{name}")
    
    logger.debug(f"Finished decorating class: {cls.__name__}")
    return cls
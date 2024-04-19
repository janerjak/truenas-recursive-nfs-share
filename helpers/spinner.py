from functools import wraps

from halo import Halo

def spinner(text: str = "Loading") -> Halo:
    def halo_fail_on_exception_wrapper(f: callable):
        @wraps(f)
        def halo_fail_on_exception_execution(*args, **kwargs):
            print(f"> {text}")
            spinner = spinner_generator(text)
            try:
                result = f(*args, **kwargs)
                spinner.succeed()
                return result
            except Exception as ex:
                spinner.fail(f"{ex}")
                raise ex
        return halo_fail_on_exception_execution
    return halo_fail_on_exception_wrapper

def spinner_generator(text: str = "Loading") -> Halo:
    return Halo(text=text, spinner='dots')
from inflect import engine as plural_engine_generator

plural_engine = plural_engine_generator()

def pl(noun : str, quantity : int):
    return plural_engine.plural_noun(noun, quantity)
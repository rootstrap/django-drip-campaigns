from lark import Lark, Transformer


class DjangoQueriesTransformer(Transformer):
    """
    Applies multiple transformations over the parsed tree
    """
    def start(self, tree):
        return tree[0]

    def OPERATOR(self, tree):
        operator_map = {
            ">": "__gt",
            "<": "__lt",
            "==": "__eq",
            "is": "",
            "null": "__isnull",
        }
        return operator_map[tree.value]

    def atom(self, a):
        (a,) = a
        return a.value

    def query(self, tree):
        if len(tree) == 3:
            return {**tree[0], **tree[2]}
        else:
            return tree[0]

    def expression(self, tree):
        return {"".join(tree[:2]): tree[2]}

    def computed(self, tree):
        return "__".join(tree)

    def string(self, s):
        (s,) = s
        return s.strip('"')

    def true(self, _):
        return True

    def false(self, _):
        return False


def translate_query(expression, grammar):
    lexer = Lark(grammar)

    parse_tree = lexer.parse(expression, start="start")
    query_dict = DjangoQueriesTransformer(
        visit_tokens=True
    ).transform(parse_tree)
    return query_dict

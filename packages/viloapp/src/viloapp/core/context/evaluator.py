#!/usr/bin/env python3
"""
When clause evaluator for context expressions.

This module provides the ability to evaluate when clause expressions
that determine when commands and shortcuts are available.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Token types for the expression parser."""

    IDENTIFIER = "IDENTIFIER"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER = "GREATER"
    LESS = "LESS"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    STRING = "STRING"
    NUMBER = "NUMBER"
    TRUE = "TRUE"
    FALSE = "FALSE"
    EOF = "EOF"


@dataclass
class Token:
    """A token in the expression."""

    type: TokenType
    value: Any
    position: int


class WhenClauseLexer:
    """Lexer for when clause expressions."""

    TOKEN_PATTERNS = [
        (r"\s+", None),  # Whitespace (skip)
        (r"&&", TokenType.AND),
        (r"\|\|", TokenType.OR),
        (r"==", TokenType.EQUALS),
        (r"!=", TokenType.NOT_EQUALS),
        (r">=", TokenType.GREATER_EQUAL),
        (r"<=", TokenType.LESS_EQUAL),
        (r"!", TokenType.NOT),  # Must come after !=
        (r">", TokenType.GREATER),
        (r"<", TokenType.LESS),
        (r"\(", TokenType.LPAREN),
        (r"\)", TokenType.RPAREN),
        (r"true", TokenType.TRUE),
        (r"false", TokenType.FALSE),
        (r'"[^"]*"', TokenType.STRING),
        (r"'[^']*'", TokenType.STRING),
        (r"-?\d+\.?\d*", TokenType.NUMBER),
        (r"[a-zA-Z_][a-zA-Z0-9_\.]*", TokenType.IDENTIFIER),
    ]

    def __init__(self, expression: str):
        """Initialize the lexer with an expression."""
        self.expression = expression
        self.position = 0
        self.tokens: list[Token] = []
        self._tokenize()

    def _tokenize(self):
        """Tokenize the expression."""
        while self.position < len(self.expression):
            matched = False

            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.expression, self.position)

                if match:
                    value = match.group(0)

                    if token_type is not None:  # Skip whitespace
                        if token_type == TokenType.STRING:
                            # Remove quotes
                            value = value[1:-1]
                        elif token_type == TokenType.NUMBER:
                            # Convert to number
                            value = float(value) if "." in value else int(value)
                        elif token_type == TokenType.TRUE:
                            value = True
                        elif token_type == TokenType.FALSE:
                            value = False

                        self.tokens.append(Token(token_type, value, self.position))

                    self.position = match.end()
                    matched = True
                    break

            if not matched:
                raise ValueError(
                    f"Invalid token at position {self.position}: {self.expression[self.position:]}"
                )

        self.tokens.append(Token(TokenType.EOF, None, self.position))


class WhenClauseParser:
    """Parser for when clause expressions."""

    def __init__(self, tokens: list[Token]):
        """Initialize the parser with tokens."""
        self.tokens = tokens
        self.current = 0

    def parse(self) -> "ASTNode":
        """Parse the tokens into an AST."""
        if not self.tokens or self.tokens[0].type == TokenType.EOF:
            return LiteralNode(True)  # Empty expression is true
        return self.parse_or()

    def parse_or(self) -> "ASTNode":
        """Parse OR expressions."""
        left = self.parse_and()

        while self.current_token().type == TokenType.OR:
            self.consume(TokenType.OR)
            right = self.parse_and()
            left = BinaryOpNode("or", left, right)

        return left

    def parse_and(self) -> "ASTNode":
        """Parse AND expressions."""
        left = self.parse_comparison()

        while self.current_token().type == TokenType.AND:
            self.consume(TokenType.AND)
            right = self.parse_comparison()
            left = BinaryOpNode("and", left, right)

        return left

    def parse_comparison(self) -> "ASTNode":
        """Parse comparison expressions."""
        left = self.parse_unary()

        token = self.current_token()
        if token.type in [
            TokenType.EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.GREATER,
            TokenType.LESS,
            TokenType.GREATER_EQUAL,
            TokenType.LESS_EQUAL,
        ]:
            op = self.consume(token.type)
            right = self.parse_unary()

            op_map = {
                TokenType.EQUALS: "==",
                TokenType.NOT_EQUALS: "!=",
                TokenType.GREATER: ">",
                TokenType.LESS: "<",
                TokenType.GREATER_EQUAL: ">=",
                TokenType.LESS_EQUAL: "<=",
            }

            return BinaryOpNode(op_map[op.type], left, right)

        return left

    def parse_unary(self) -> "ASTNode":
        """Parse unary expressions."""
        if self.current_token().type == TokenType.NOT:
            self.consume(TokenType.NOT)
            return UnaryOpNode("not", self.parse_unary())

        return self.parse_primary()

    def parse_primary(self) -> "ASTNode":
        """Parse primary expressions."""
        token = self.current_token()

        if token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            node = self.parse_or()
            self.consume(TokenType.RPAREN)
            return node

        if token.type == TokenType.IDENTIFIER:
            value = self.consume(TokenType.IDENTIFIER).value
            return IdentifierNode(value)

        if token.type in [
            TokenType.STRING,
            TokenType.NUMBER,
            TokenType.TRUE,
            TokenType.FALSE,
        ]:
            value = self.consume(token.type).value
            return LiteralNode(value)

        raise ValueError(f"Unexpected token: {token}")

    def current_token(self) -> Token:
        """Get the current token."""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return self.tokens[-1]  # EOF

    def consume(self, expected_type: TokenType) -> Token:
        """Consume a token of the expected type."""
        token = self.current_token()
        if token.type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {token.type}")
        self.current += 1
        return token


# AST Node classes


class ASTNode:
    """Base class for AST nodes."""

    pass


class IdentifierNode(ASTNode):
    """Node for context identifiers."""

    def __init__(self, name: str):
        self.name = name


class LiteralNode(ASTNode):
    """Node for literal values."""

    def __init__(self, value: Any):
        self.value = value


class UnaryOpNode(ASTNode):
    """Node for unary operations."""

    def __init__(self, op: str, operand: ASTNode):
        self.op = op
        self.operand = operand


class BinaryOpNode(ASTNode):
    """Node for binary operations."""

    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right


class WhenClauseEvaluator:
    """Evaluator for when clause expressions."""

    @staticmethod
    def evaluate(expression: Optional[str], context: dict[str, Any]) -> bool:
        """
        Evaluate a when clause expression.

        Args:
            expression: When clause expression (None means always true)
            context: Context dictionary for evaluation

        Returns:
            True if the expression evaluates to true

        Examples:
            evaluate("editorFocus", {"editorFocus": True}) -> True
            evaluate("!terminalFocus", {"terminalFocus": False}) -> True
            evaluate("editorFocus && hasSelection", {...}) -> depends on context
        """
        if not expression:
            return True

        try:
            # Lex and parse the expression
            lexer = WhenClauseLexer(expression)
            parser = WhenClauseParser(lexer.tokens)
            ast = parser.parse()

            # Evaluate the AST
            return WhenClauseEvaluator._evaluate_node(ast, context)

        except Exception as e:
            logger.error(f"Error evaluating when clause '{expression}': {e}")
            return False

    @staticmethod
    def _evaluate_node(node: ASTNode, context: dict[str, Any]) -> Any:
        """Evaluate an AST node."""
        if isinstance(node, LiteralNode):
            return node.value

        if isinstance(node, IdentifierNode):
            # Handle nested properties (e.g., "config.editor.fontSize")
            parts = node.name.split(".")
            value = context

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, False)
                else:
                    return False

            # Return the actual value (don't force to boolean for comparisons)
            return value

        if isinstance(node, UnaryOpNode):
            operand = WhenClauseEvaluator._evaluate_node(node.operand, context)

            if node.op == "not":
                return not operand

            raise ValueError(f"Unknown unary operator: {node.op}")

        if isinstance(node, BinaryOpNode):
            left = WhenClauseEvaluator._evaluate_node(node.left, context)
            right = WhenClauseEvaluator._evaluate_node(node.right, context)

            if node.op == "and":
                return left and right
            elif node.op == "or":
                return left or right
            elif node.op == "==":
                return left == right
            elif node.op == "!=":
                return left != right
            elif node.op == ">":
                return left > right
            elif node.op == "<":
                return left < right
            elif node.op == ">=":
                return left >= right
            elif node.op == "<=":
                return left <= right

            raise ValueError(f"Unknown binary operator: {node.op}")

        raise ValueError(f"Unknown node type: {type(node)}")


def test_evaluator():
    """Test the when clause evaluator."""
    context = {
        "editorFocus": True,
        "terminalFocus": False,
        "hasSelection": True,
        "paneCount": 3,
        "platform": "linux",
    }

    tests = [
        ("editorFocus", True),
        ("!terminalFocus", True),
        ("editorFocus && hasSelection", True),
        ("terminalFocus || hasSelection", True),
        ("paneCount > 2", True),
        ("paneCount == 3", True),
        ("platform == 'linux'", True),
        ("platform != 'windows'", True),
        ("(editorFocus || terminalFocus) && hasSelection", True),
    ]

    for expression, expected in tests:
        result = WhenClauseEvaluator.evaluate(expression, context)
        status = "✓" if result == expected else "✗"
        print(f"{status} {expression} -> {result} (expected {expected})")


if __name__ == "__main__":
    test_evaluator()

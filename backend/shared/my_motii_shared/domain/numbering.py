"""Document-number value and deterministic formatting helpers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentNumber:
	branch_code: str
	document_type: str
	fiscal_year: int
	sequence: int
	width: int = 5

	def __post_init__(self) -> None:
		if not self.branch_code or not self.document_type:
			raise ValueError("Branch code and document type are required.")
		if self.fiscal_year < 1 or self.sequence < 1 or self.width < 1:
			raise ValueError("Fiscal year, sequence, and width must be positive integers.")

	def __str__(self) -> str:
		return f"{self.branch_code}-{self.document_type}-{self.fiscal_year}-{self.sequence:0{self.width}d}"


def format_document_number(
	branch_code: str,
	document_type: str,
	fiscal_year: int,
	sequence: int,
	*,
	width: int = 5,
) -> str:
	return str(DocumentNumber(branch_code, document_type, fiscal_year, sequence, width))
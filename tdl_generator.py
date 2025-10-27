"""
LLM-based TDL Document Generator
Uses Gemini API to generate complete TDL documents from analyzed requirements.
"""
from llm_client import GeminiClient
from analyzer import RequirementAnalysis


class LLMTDLGenerator:
    """Generates TDL documents using LLM."""

    def __init__(self, api_key: str = None):
        """
        Initialize generator with LLM client.

        Args:
            api_key: Gemini API key. If None, reads from environment.
        """
        self.llm_client = GeminiClient(api_key)

    def generate(self, analysis: RequirementAnalysis) -> str:
        """
        Generate TDL document from requirement analysis using LLM.

        Args:
            analysis: Analyzed requirement

        Returns:
            Complete TDL document as string

        Raises:
            Exception: If TDL generation fails
        """
        print("\n[LLM] LLM generating TDL document...")

        try:
            # Call LLM to generate TDL
            tdl_content = self.llm_client.generate_tdl(
                task_description=analysis.task_description,
                actions=analysis.actions,
                objects=analysis.objects,
                locations=analysis.locations,
                constraints=analysis.constraints,
                coordinates=analysis.coordinates  # NEW: Pass coordinates
            )

            print("[OK] LLM TDL generation completed")
            return tdl_content

        except Exception as e:
            raise Exception(f"LLM TDL generation failed: {e}")

    def validate_tdl(self, tdl_content: str) -> bool:
        """
        Validate TDL document structure.

        Args:
            tdl_content: TDL document to validate

        Returns:
            True if valid, False otherwise
        """
        # Check for required sections
        required_sections = ["HEADER", "END_HEADER", "GOAL", "END_GOAL"]

        for section in required_sections:
            if section not in tdl_content:
                print(f"[WARNING]  Warning: Missing required section '{section}'")
                return False

        # Check for three goals
        goal_count = tdl_content.count("GOAL ")
        if goal_count < 3:
            print(f"[WARNING]  Warning: Expected 3 goals, found {goal_count}")
            return False

        return True

    def post_process_tdl(self, tdl_content: str) -> str:
        """
        Post-process and clean TDL content.

        Args:
            tdl_content: Raw TDL content from LLM

        Returns:
            Cleaned TDL content
        """
        # Remove any markdown code blocks if present
        if "```" in tdl_content:
            lines = tdl_content.split("\n")
            cleaned_lines = []
            in_code_block = False

            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if not in_code_block or line.strip():
                    cleaned_lines.append(line)

            tdl_content = "\n".join(cleaned_lines)

        # Ensure consistent line endings
        tdl_content = tdl_content.replace("\r\n", "\n")

        # Remove excessive blank lines
        while "\n\n\n" in tdl_content:
            tdl_content = tdl_content.replace("\n\n\n", "\n\n")

        return tdl_content.strip() + "\n"

    def generate_with_validation(self, analysis: RequirementAnalysis) -> str:
        """
        Generate TDL with validation and post-processing.

        Args:
            analysis: Analyzed requirement

        Returns:
            Complete and validated TDL document

        Raises:
            Exception: If generation or validation fails
        """
        # Generate TDL
        tdl_content = self.generate(analysis)

        # Post-process
        tdl_content = self.post_process_tdl(tdl_content)

        # Validate
        if not self.validate_tdl(tdl_content):
            print("[WARNING]  Warning: TDL validation failed, but continuing...")

        return tdl_content

    def regenerate_with_feedback(
        self,
        analysis: RequirementAnalysis,
        previous_tdl: str,
        feedback: str
    ) -> str:
        """
        Regenerate TDL based on user feedback.

        Args:
            analysis: Original requirement analysis
            previous_tdl: Previously generated TDL
            feedback: User feedback on what to improve

        Returns:
            Regenerated TDL document
        """
        print(f"\n[LLM] Regenerating TDL based on feedback...")

        prompt = f"""이전에 생성한 TDL 문서를 개선해주세요.

원래 작업:
- 작업 설명: {analysis.task_description}
- 동작: {', '.join(analysis.actions)}
- 대상 물체: {', '.join(analysis.objects)}
- 위치: {', '.join(analysis.locations)}
- 제약 조건: {', '.join(analysis.constraints)}

이전 TDL:
{previous_tdl}

사용자 피드백:
{feedback}

피드백을 반영하여 개선된 TDL 문서를 생성해주세요. TDL 문서만 출력하고 다른 설명은 포함하지 마세요."""

        try:
            response = self.llm_client.generate_content(prompt, temperature=0.5, max_tokens=3000)
            tdl_content = self.post_process_tdl(response)
            print("[OK] TDL regeneration completed")
            return tdl_content
        except Exception as e:
            raise Exception(f"TDL regeneration failed: {e}")

    def explain_tdl(self, tdl_content: str) -> str:
        """
        Generate human-readable explanation of TDL document using LLM.

        Args:
            tdl_content: TDL document to explain

        Returns:
            Human-readable explanation
        """
        prompt = f"""다음 TDL(Task Description Language) 문서를 일반인이 이해할 수 있도록 한국어로 설명해주세요.

TDL 문서:
{tdl_content}

설명에 포함할 내용:
1. 전체 작업의 목적
2. 주요 단계별 설명
3. 각 GOAL의 역할
4. 중요한 명령어들의 의미

간결하고 명확하게 설명해주세요."""

        try:
            explanation = self.llm_client.generate_content(prompt, temperature=0.3, max_tokens=4000)
            return explanation.strip()
        except Exception as e:
            return f"설명 생성 실패: {e}"

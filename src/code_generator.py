"""智能代码生成引擎 - v4.0院士版
从研究空白自动生成可执行代码
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# 尝试导入 langchain，如果没有安装则使用占位符
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None

from src.db_manager import DatabaseManager
from src.database import ResearchGap, GeneratedCode


class CodeGenerationStrategy:
    """代码生成策略"""

    STRATEGIES = {
        "method_improvement": {
            "name": "方法改进",
            "description": "基于现有方法进行改进",
            "template": "改进现有方法以解决特定问题",
            "output": "改进后的算法实现代码"
        },
        "new_method": {
            "name": "新方法提出",
            "description": "设计全新的方法",
            "template": "针对问题设计新方法",
            "output": "完整的方法实现+测试"
        },
        "dataset_creation": {
            "name": "数据集构建",
            "description": "创建满足特定需求的数据集",
            "template": "生成数据集创建代码",
            "output": "数据生成脚本"
        },
        "experiment_design": {
            "name": "实验设计",
            "description": "设计验证性实验",
            "template": "设计实验方案",
            "output": "实验代码+评估脚本"
        },
        "model_implementation": {
            "name": "模型实现",
            "description": "实现具体的模型",
            "template": "实现指定模型",
            "output": "模型代码+训练脚本"
        },
        "algorithm_optimization": {
            "name": "算法优化",
            "description": "优化算法性能",
            "template": "优化算法以提高效率",
            "output": "优化后的算法代码"
        }
    }


class CodeGenerator:
    """智能代码生成器"""

    def __init__(
        self,
        llm: ChatOpenAI = None,
        db_manager: DatabaseManager = None
    ):
        """
        初始化代码生成器

        Args:
            llm: LLM实例
            db_manager: 数据库管理器
        """
        if llm:
            self.llm = llm
        elif LANGCHAIN_AVAILABLE and ChatOpenAI:
            self.llm = ChatOpenAI(
                model='glm-4-air',
                temperature=0.2,  # 代码生成需要较低温度
                max_tokens=16000
            )
        else:
            self.llm = None

        self.db = db_manager or DatabaseManager()

        # 代码生成模板
        self.system_prompt = """你是一位世界顶级的深度学习框架开发者和算法工程师。

你的专长包括：
1. 深度学习框架（PyTorch、TensorFlow、JAX）
2. 机器学习算法（经典到前沿）
3. 代码质量和最佳实践
4. 软件工程规范

**代码生成要求**：
1. 代码必须可以直接运行，无语法错误
2. 包含完整的文档字符串（Google风格）
3. 包含类型提示（Type Hints）
4. 包含单元测试
5. 遵循框架最佳实践
6. 代码结构清晰，模块化
7. 包含必要的注释
8. 处理边界情况

**输出格式**：
仅输出代码，不要任何解释或markdown标记。
"""

    async def generate_code_async(
        self,
        research_gap: ResearchGap,
        strategy: str = "method_improvement",
        language: str = "python",
        framework: str = "pytorch",
        user_prompt: str = None
    ) -> Dict[str, Any]:
        """
        异步生成代码

        Args:
            research_gap: 研究空白对象
            strategy: 代码生成策略
            language: 编程语言
            framework: 框架
            user_prompt: 用户自定义提示

        Returns:
            Dict: 生成的代码数据
        """
        if not self.llm or not LANGCHAIN_AVAILABLE:
            raise ValueError("LLM功能未启用，无法生成代码")

        # 构建提示词
        prompt = self._build_code_generation_prompt(
            research_gap, strategy, language, framework, user_prompt
        )

        # 调用LLM生成代码
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.invoke,
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
        )

        code = response.content

        # 提取代码（如果有markdown代码块）
        code = self._extract_code_from_markdown(code)

        # 生成依赖列表
        dependencies = self._extract_dependencies(code, framework)

        # 生成文档字符串
        docstring = self._generate_docstring(research_gap, strategy)

        # 构建返回数据
        code_data = {
            'code': code,
            'language': language,
            'framework': framework,
            'dependencies': dependencies,
            'docstring': docstring,
            'user_prompts': [user_prompt] if user_prompt else [],
            'current_version': 1,
            'status': 'generated',
            'quality_score': self._assess_code_quality(code)
        }

        return code_data

    def _build_code_generation_prompt(
        self,
        research_gap,
        strategy: str,
        language: str,
        framework: str,
        user_prompt: str = None
    ) -> str:
        """构建代码生成提示词
        
        Args:
            research_gap: 研究空白对象或字典
        """

        # 获取策略信息
        strategy_info = CodeGenerationStrategy.STRATEGIES.get(
            strategy,
            CodeGenerationStrategy.STRATEGIES["method_improvement"]
        )

        # 处理字典类型输入
        if isinstance(research_gap, dict):
            gap_type = research_gap.get('gap_type', 'methodological')
            description = research_gap.get('description', '')
            importance = research_gap.get('importance', 'medium')
            difficulty = research_gap.get('difficulty', 'medium')
            potential_approach = research_gap.get('potential_approach', '')
            expected_impact = research_gap.get('expected_impact', '')
        else:
            # 对象类型访问
            gap_type = getattr(research_gap, 'gap_type', 'methodological')
            description = getattr(research_gap, 'description', '')
            importance = getattr(research_gap, 'importance', 'medium')
            difficulty = getattr(research_gap, 'difficulty', 'medium')
            potential_approach = getattr(research_gap, 'potential_approach', '')
            expected_impact = getattr(research_gap, 'expected_impact', '')

        # 基础提示词
        prompt = f"""# 代码生成任务

## 研究空白
**类型**: {gap_type}
**描述**: {description}
**重要性**: {importance}
**难度**: {difficulty}

## 潜在解决方法
{potential_approach}

## 预期影响
{expected_impact}

## 代码生成策略
**策略**: {strategy_info['name']}
**描述**: {strategy_info['description']}

## 技术要求
- **编程语言**: {language}
- **框架**: {framework}
- **代码质量**: 生产级，可直接运行

## 代码结构要求

1. **导入和依赖**：清晰的import语句
2. **类/函数定义**：遵循命名规范
3. **文档字符串**：Google风格的完整文档
4. **类型提示**：所有函数参数和返回值
5. **单元测试**：包含测试函数
6. **示例使用**：包含使用示例

## 具体要求
"""

        # 根据策略添加具体要求
        if strategy == "method_improvement":
            prompt += f"""
基于以下潜在方法，生成改进的实现：

{research_gap.potential_approach}

实现要求：
1. 保持原方法的核心思想
2. 针对指出的空白进行改进
3. 提升性能或扩展功能
4. 向后兼容
"""

        elif strategy == "new_method":
            prompt += f"""
设计全新方法来解决以下问题：

{research_gap.description}

实现要求：
1. 创新性设计
2. 理论依据清晰
3. 可实现性强
4. 包含完整实现
"""

        elif strategy == "model_implementation":
            prompt += f"""
实现以下模型：

{research_gap.potential_approach}

实现要求：
1. 继承框架基类
2. 实现核心方法
3. 支持GPU加速
4. 包含训练和评估脚本
"""

        elif strategy == "dataset_creation":
            prompt += f"""
创建数据集：

{research_gap.description}

实现要求：
1. 数据生成/加载逻辑
2. 数据预处理
3. 数据增强
4. 批处理支持
"""

        elif strategy == "experiment_design":
            prompt += f"""
设计实验：

{research_gap.description}

实现要求：
1. 实验设置
2. 评估指标
3. 结果记录
4. 可视化代码
"""

        elif strategy == "algorithm_optimization":
            prompt += f"""
优化算法：

{research_gap.description}

实现要求：
1. 优化目标明确
2. 性能对比
3. 复杂度分析
4. 基准测试
"""

        # 添加用户自定义提示
        if user_prompt:
            prompt += f"""

## 用户自定义要求
{user_prompt}
"""

        prompt += """

## 输出格式
请直接输出完整的可执行代码，不要包含任何解释文字。
代码应该包含：
1. 所有必要的import
2. 完整的类/函数实现
3. 文档字符串
4. 类型提示
5. 单元测试
6. 使用示例

开始生成代码：
"""

        return prompt

    def _extract_code_from_markdown(self, text: str) -> str:
        """从markdown中提取代码"""
        if "```python" in text:
            start = text.find("```python") + 9
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        return text.strip()

    def _extract_dependencies(self, code: str, framework: str) -> str:
        """提取依赖列表"""
        dependencies = []

        # 常见依赖映射
        dependency_map = {
            'torch': 'torch',
            'tensorflow': 'tensorflow',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'sklearn': 'scikit-learn',
            'matplotlib': 'matplotlib',
            'seaborn': 'seaborn',
            'transformers': 'transformers',
            'datasets': 'datasets',
        }

        # 分析import语句
        for line in code.split('\n'):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                for module, package in dependency_map.items():
                    if module in line:
                        if package not in dependencies:
                            dependencies.append(package)

        # 框架特定依赖
        if framework == 'pytorch' and 'torch' not in dependencies:
            dependencies.insert(0, 'torch')
        elif framework == 'tensorflow' and 'tensorflow' not in dependencies:
            dependencies.insert(0, 'tensorflow')

        return '\n'.join([f'{dep}>=latest' for dep in dependencies])

    def _generate_docstring(self, research_gap, strategy: str) -> str:
        """生成代码文档字符串
        
        Args:
            research_gap: 研究空白对象或字典
        """
        # 处理字典类型输入
        if isinstance(research_gap, dict):
            gap_type = research_gap.get('gap_type', 'methodological')
            description = research_gap.get('description', '')
            potential_approach = research_gap.get('potential_approach', '')
            expected_impact = research_gap.get('expected_impact', '')
        else:
            gap_type = getattr(research_gap, 'gap_type', 'methodological')
            description = getattr(research_gap, 'description', '')
            potential_approach = getattr(research_gap, 'potential_approach', '')
            expected_impact = getattr(research_gap, 'expected_impact', '')

        return f"""
# 自动生成的代码 - v4.0院士级系统

## 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 策略: {strategy}
- 语言: python

## 研究空白
- 类型: {gap_type}
- 描述: {description}

## 潜在解决方法
{potential_approach}

## 预期影响
{expected_impact}

## 使用说明
此代码由AI自动生成，建议：
1. 仔细阅读并理解代码逻辑
2. 运行单元测试验证功能
3. 根据具体需求进行调整
4. 在实际数据上测试性能

---

**注意**: 代码可能需要根据您的具体环境进行微调。
"""

    def _assess_code_quality(self, code: str) -> float:
        """评估代码质量（简单版）"""
        score = 0.0

        # 检查文档字符串
        if '"""' in code or "'''" in code:
            score += 0.2

        # 检查类型提示
        if 'def ' in code and '->' in code:
            score += 0.15

        # 检查类定义
        if 'class ' in code:
            score += 0.1

        # 检查错误处理
        if 'try:' in code and 'except' in code:
            score += 0.15

        # 检查测试
        if 'test' in code.lower():
            score += 0.2

        # 检查注释
        if '#' in code:
            score += 0.1

        # 检查代码长度（太短或太长都不好）
        lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        if 50 <= len(lines) <= 500:
            score += 0.1

        return min(score, 1.0)

    async def modify_code_async(
        self,
        code_id: int,
        user_prompt: str,
        db_manager: DatabaseManager = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据用户提示修改代码

        Args:
            code_id: 代码ID
            user_prompt: 用户修改提示
            db_manager: 数据库管理器

        Returns:
            修改后的代码字典
        """
        db = db_manager or self.db

        # 获取原代码
        code_record = db.get_code(code_id)
        if not code_record:
            return None

        # 获取关联的研究空白
        gap_id = code_record.get('gap_id')
        if not gap_id:
            return None

        # 构建修改提示
        modify_prompt = f"""# 代码修改任务

## 原始代码
```python
{code_record.get('code', '')}
```

## 用户修改要求
{user_prompt}

## 修改要求
1. 保持代码的整体结构
2. 仅修改用户指定的部分
3. 确保修改后的代码仍然可以运行
4. 更新相关的文档字符串
5. 保持代码风格一致

请输出修改后的完整代码：
"""

        if not self.llm or not LANGCHAIN_AVAILABLE:
            raise ValueError("LLM功能未启用，无法修改代码")

        # 调用LLM修改代码
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.invoke,
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=modify_prompt)
            ]
        )

        new_code = self._extract_code_from_markdown(response.content)

        # 获取当前版本和提示历史
        current_version = code_record.get('current_version', 1)
        user_prompts = code_record.get('user_prompts', []) or []

        # 更新主代码记录
        update_data = {
            'code': new_code,
            'user_prompts': user_prompts + [user_prompt],
            'current_version': current_version + 1,
            'updated_at': datetime.utcnow()
        }

        updated_code = db.update_code(code_id, update_data)

        return updated_code

    async def generate_code_with_interaction(
        self,
        research_gap: ResearchGap,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        交互式代码生成（支持多轮迭代）

        Args:
            research_gap: 研究空白
            max_iterations: 最大迭代次数

        Returns:
            最终代码和迭代历史
        """
        iteration_history = []
        current_code = None

        for iteration in range(max_iterations):
            print(f"\n[代码生成] 迭代 {iteration + 1}/{max_iterations}")

            # 生成代码
            if iteration == 0:
                # 第一次生成
                code_data = await self.generate_code_async(research_gap)
            else:
                # 获取用户反馈（在实际应用中，这里应该等待用户输入）
                # 这里简化为自动改进
                user_feedback = "请优化代码性能和可读性"

                code_data = await self.generate_code_async(
                    research_gap,
                    user_prompt=user_feedback
                )

            current_code = code_data
            iteration_history.append({
                'iteration': iteration + 1,
                'timestamp': datetime.now().isoformat(),
                'code': code_data['code'],
                'quality_score': code_data['quality_score']
            })

            print(f"  质量评分: {code_data['quality_score']:.2f}")

            # 如果质量足够高，停止迭代
            if code_data['quality_score'] >= 0.85:
                print(f"  ✓ 代码质量达标，停止迭代")
                break

        return {
            'final_code': current_code,
            'iteration_history': iteration_history,
            'total_iterations': len(iteration_history)
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def generate_code_for_gap(
    gap_id: int,
    db_manager: DatabaseManager = None
) -> Optional[Dict[str, Any]]:
    """
    便捷函数：为研究空白生成代码

    Args:
        gap_id: 研究空白ID
        db_manager: 数据库管理器

    Returns:
        生成的代码字典
    """
    db = db_manager or DatabaseManager()

    # 使用get_research_gap获取研究空白详情
    gap_dict = db.get_research_gap(gap_id)

    if not gap_dict:
        return None

    # 将字典转换为SimpleNamespace对象以兼容现有代码
    from types import SimpleNamespace
    gap = SimpleNamespace(**gap_dict)

    generator = CodeGenerator(db_manager=db)
    code_data = await generator.generate_code_async(gap)

    code_data['gap_id'] = gap_id
    code_record = db.create_generated_code(code_data)

    return code_record

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from langchain_sarvam import ChatSarvam
from tools import web_search
import os
load_dotenv()


model = ChatSarvam(model="sarvam-105b",
                   reasoning_effort="low",
                   max_tokens=4096
                   )


writer_promt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert Research Report Writer.

Your responsibility is to transform the provided research into a professional, structured report.

Rules:
- Use ONLY the provided research.
- Do NOT invent facts, statistics, dates, or sources.
- If information is missing, state that it is unavailable in the provided research.
- Remove duplicate information.
- Keep the report objective, factual, and well organized.
- Write in Markdown.
- If multiple sources disagree, mention the conflict instead of choosing one."""
    ),
    (
        "human",
        """Generate a comprehensive research report.

Topic:
{topic}

Research Gathered:
{research}

Follow this structure exactly:

# {topic}

## Introduction
Provide an overview of the topic and explain its significance.

## Key Findings
Write at least 3 detailed findings.
For each finding:
- Use a clear heading.
- Explain the concept.
- Include supporting facts, statistics, or examples from the research.

## Analysis
Summarize patterns, trends, opportunities, challenges, and important insights found in the research.

## Conclusion
Provide a concise summary of the most important takeaways.

## Sources
List every unique URL found in the research as bullet points.

Requirements:
- Do not hallucinate.
- Do not repeat the same information.
- Preserve all important numbers, names, and dates.
- Use professional and easy-to-read language.
- Produce a report that is suitable for publication."""
    )
])

writer_chain = writer_promt | model | StrOutputParser()

critics_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert Research Report Critic.

Your role is to critically evaluate research reports with fairness, objectivity, and constructive feedback.

Rules:
- Be honest and specific.
- Judge only the report that is provided.
- Do not invent missing information.
- Focus on quality, organization, evidence, clarity, and completeness.
- Point out both strengths and weaknesses.
- If a section is missing, mention it explicitly.
- Keep feedback concise but actionable."""
    ),
    (
        "human",
        """Review the research report below.

Report:
{report}

Evaluate it using the following criteria:
- Structure and organization
- Clarity and readability
- Coverage of the topic
- Quality of explanations
- Use of evidence and supporting facts
- Logical flow
- Professional writing style
- Overall usefulness

Respond in exactly this format:

# Research Report Review

## Overall Score
X/10

## Strengths
- ...
- ...
- ...

## Areas for Improvement
- ...
- ...
- ...

## Missing or Weak Sections
- ...

## Suggestions
- ...
- ...
- ...

## Verdict
One concise sentence summarizing the overall quality of the report.
"""
    )
])

critic_chain = critics_prompt | model | StrOutputParser()

import re
from datetime import date, timedelta
from typing import Any

from app.models import Goal
from app.schemas import DraftMilestone, DraftTask, PlanDraft

def normalize_goal_intent(goal: Goal) -> str:
    # Correct only clear typos for planner routing; never write this value to the goal.
    intent = " ".join(f"{goal.title} {goal.description}".casefold().split())
    intent = re.sub(r"\bbacka\s+nd\b", "back and", intent)
    return re.sub(r"\bfrnot\b", "front", intent)


def build_fallback_draft(goal: Goal, available_minutes: int) -> PlanDraft:
    style = goal.learning_style.strip()
    style_hint = f" using your {style[:60]} learning style" if style else ""
    learner_context = f"Start from your current level: {goal.skill_level}."
    if goal.learning_constraints.strip():
        learner_context += f" Plan around: {goal.learning_constraints.strip()[:1700]}"
    intent = normalize_goal_intent(goal)
    is_python = bool(re.search(r"\bpython\b", intent))
    is_javascript = bool(
        re.search(r"\b(java\s*script|javascript|js)\b|\bfront[\s-]?end\b|\bweb\s+development\b", intent)
    )
    is_english = bool(re.search(r"\benglish\b", intent))
    is_ai_website = bool(
        re.search(r"\b(?:ai|artificial intelligence)\s+agents?\b", intent)
        and re.search(r"\bwebsite|web site|webpage|web page\b", intent)
    )
    focus = (
        "Python" if is_python
        else "JavaScript" if is_javascript
        else "English" if is_english
        else "a website built with AI tools" if is_ai_website
        else goal.title.strip() or goal.description.strip()
    ).rstrip(".!?")[:100]
    is_beginner = any(
        marker in goal.skill_level.casefold()
        for marker in ("beginner", "starting", "just getting", "new to", "novice")
    )

    if is_python:
        if is_beginner:
            foundation_title = "Practice Python values, conditionals, and loops"
            foundation_criteria = "Complete three runnable Python exercises and explain what each one does in a short note."
            next_title = "Write and test a reusable Python function"
            next_criteria = "Create one Python function with a clear purpose and verify it with at least two inputs."
        else:
            foundation_title = "Practice Python data structures and organize a small dataset"
            foundation_criteria = "Write a Python script that transforms a sample dataset and verify its output against two expected cases."
            next_title = "Refactor the Python script into tested functions"
            next_criteria = "Separate the script into reusable functions and add at least two passing tests."
        milestones = [
            DraftMilestone(
                title="Set up a Python learning workspace",
                description=f"{learner_context} Prepare a Python environment and connect the exercises to your goal.",
                tasks=[
                    DraftTask(
                        title="Set up Python and run a first script",
                        estimated_minutes=45,
                        completion_criteria="Run a short Python script successfully and save it in a clearly named project folder.",
                    ),
                    DraftTask(
                        title=f"Create a Python practice checklist{style_hint}",
                        estimated_minutes=45,
                        completion_criteria=f"List three Python concepts to practice and one small result connected to: {focus}.",
                    ),
                ],
            ),
            DraftMilestone(
                title="Build Python foundations",
                description=f"{learner_context} Practice concepts that can be used in a small Python program.",
                tasks=[
                    DraftTask(
                        title=foundation_title,
                        estimated_minutes=45,
                        completion_criteria=foundation_criteria,
                    ),
                    DraftTask(
                        title=next_title,
                        estimated_minutes=45,
                        completion_criteria=next_criteria,
                    ),
                ],
            ),
            DraftMilestone(
                title="Build a Python result for your goal",
                description=f"{learner_context} Apply the new skills to a small result related to {focus}.",
                tasks=[
                    DraftTask(
                        title=f"Build a small Python project for: {focus[:70]}",
                        estimated_minutes=60,
                        completion_criteria=f"Save a working Python project that completes one clearly stated task related to: {focus}.",
                    ),
                    DraftTask(
                        title="Test and document the Python project",
                        estimated_minutes=45,
                        completion_criteria="Run at least two checks, fix one issue or improve one detail, and write brief instructions to run the Python project.",
                    ),
                ],
            ),
        ]
    elif is_javascript:
        is_full_stack = bool(
            re.search(
                r"\b(?:back and front end|front end and back end|full[\s-]?stack)\b",
                intent,
            )
        )
        if is_full_stack:
            milestones = [
                DraftMilestone(
                    title="Set up a JavaScript front-end and back-end project",
                    description=f"{learner_context} Create a small full-stack JavaScript workspace that fits your available time.",
                    tasks=[
                        DraftTask(
                            title="Create a browser page and a minimal Node.js server",
                            estimated_minutes=60,
                            completion_criteria="Run a local HTML/JavaScript page and a Node.js server, and verify that each starts successfully.",
                        ),
                        DraftTask(
                            title="Map one user action to a front-end and back-end result",
                            estimated_minutes=30,
                            completion_criteria="Write down one user action, the browser response, and the server response your small app must produce.",
                        ),
                    ],
                ),
                DraftMilestone(
                    title="Connect the JavaScript front end to a back-end endpoint",
                    description=f"{learner_context} Build one useful vertical slice from the browser UI through the server and back.",
                    tasks=[
                        DraftTask(
                            title="Build a focused JavaScript front-end interaction",
                            estimated_minutes=60,
                            completion_criteria="Implement a browser interaction that collects input, provides a visible response, and handles empty input.",
                        ),
                        DraftTask(
                            title="Add a Node.js endpoint and connect it to the front end",
                            estimated_minutes=60,
                            completion_criteria="Create one Node.js endpoint, call it from the browser, and verify the expected response appears in the page.",
                        ),
                    ],
                ),
                DraftMilestone(
                    title="Test and improve the full-stack JavaScript app",
                    description=f"{learner_context} Check both sides of the app and improve it based on observed behavior.",
                    tasks=[
                        DraftTask(
                            title="Test the browser interaction and Node.js endpoint",
                            estimated_minutes=45,
                            completion_criteria="Test valid and invalid inputs, confirm the endpoint response, and record one front-end and one back-end issue if present.",
                        ),
                        DraftTask(
                            title="Fix one full-stack issue and retest the user flow",
                            estimated_minutes=45,
                            completion_criteria="Fix the highest-priority issue found and repeat the browser-to-server flow to confirm it works.",
                        ),
                    ],
                ),
            ]
        elif is_beginner:
            first_task = "Practice JavaScript variables, values, and conditional logic"
            first_criteria = "Write three small JavaScript examples using variables and conditionals, then explain their outputs."
            second_task = "Write JavaScript functions and handle a button click"
            second_criteria = "Add a JavaScript function to a simple page and verify its result from a button click."
        else:
            first_task = "Use JavaScript array methods to transform sample data"
            first_criteria = "Transform a sample array with JavaScript map, filter, or reduce and verify the expected output."
            second_task = "Build a JavaScript interaction with validation and error handling"
            second_criteria = "Implement one browser interaction and verify its normal, empty, and invalid-input cases."
        if not is_full_stack:
            milestones = [
            DraftMilestone(
                title="Prepare a JavaScript practice page",
                description=f"{learner_context} Work in a browser page so you can inspect JavaScript behavior as you learn{style_hint}.",
                tasks=[
                    DraftTask(
                        title="Create an HTML page and run a linked JavaScript file",
                        estimated_minutes=45,
                        completion_criteria="Open a local HTML page, load an external JavaScript file, and confirm a visible or console result.",
                    ),
                    DraftTask(
                        title="Choose a practical JavaScript outcome for your goal",
                        estimated_minutes=30,
                        completion_criteria="Choose one small browser result that supports your goal and write down how you will verify it.",
                    ),
                ],
            ),
            DraftMilestone(
                title="Practice JavaScript language fundamentals",
                description=f"{learner_context} Plan around: {goal.learning_constraints.strip()[:1700] or 'your available time'}. Use JavaScript examples that build toward a working browser interaction.",
                tasks=[
                    DraftTask(
                        title=first_task,
                        estimated_minutes=45,
                        completion_criteria=first_criteria,
                    ),
                    DraftTask(
                        title=second_task,
                        estimated_minutes=45,
                        completion_criteria=second_criteria,
                    ),
                ],
            ),
            DraftMilestone(
                title="Build a JavaScript feature for your goal",
                description=f"{learner_context} Apply JavaScript in a small browser feature related to {focus}.",
                tasks=[
                    DraftTask(
                        title="Build a small JavaScript feature for your goal",
                        estimated_minutes=60,
                        completion_criteria="Deliver a browser feature using JavaScript and verify it demonstrates a concrete part of your goal.",
                    ),
                    DraftTask(
                        title="Test the JavaScript feature and note one improvement",
                        estimated_minutes=45,
                        completion_criteria="Test the feature with at least two inputs or actions, fix one issue, and note one next improvement.",
                    ),
                ],
            ),
            ]
    elif is_english:
        if is_beginner:
            first_task = "Practice 10 English phrases for a familiar situation"
            first_criteria = "Say or write ten useful English phrases for one situation and check their meaning and pronunciation."
            second_task = "Listen to a short English dialogue and repeat key lines"
            second_criteria = "Listen to a short English dialogue, identify five familiar words, and repeat three complete lines."
        else:
            first_task = "Read a short English article and summarize its main points"
            first_criteria = "Read a short English article and write or say a summary that includes its main idea and three supporting details."
            second_task = "Practice an English conversation and refine your responses"
            second_criteria = "Complete a five-minute English conversation practice and revise three responses for clarity and natural phrasing."
        milestones = [
            DraftMilestone(
                title="Set an English practice routine",
                description=f"{learner_context} Use short English listening and speaking activities that fit your schedule.",
                tasks=[
                    DraftTask(
                        title=f"Choose a practical English situation related to: {focus[:65]}",
                        estimated_minutes=30,
                        completion_criteria=f"Choose one real situation connected to {focus} and write five English words or phrases you will need.",
                    ),
                    DraftTask(
                        title=f"Create a short daily English practice set{style_hint}",
                        estimated_minutes=30,
                        completion_criteria="Select a short English audio, reading, or speaking exercise and schedule three practice sessions.",
                    ),
                ],
            ),
            DraftMilestone(
                title="Build English listening and expression",
                description=f"{learner_context} Plan around: {goal.learning_constraints.strip()[:1700] or 'your available time'}. Practice understanding and producing English at a manageable level.",
                tasks=[
                    DraftTask(
                        title=first_task,
                        estimated_minutes=45,
                        completion_criteria=first_criteria,
                    ),
                    DraftTask(
                        title=second_task,
                        estimated_minutes=45,
                        completion_criteria=second_criteria,
                    ),
                ],
            ),
            DraftMilestone(
                title="Use English in a goal-related conversation",
                description=f"{learner_context} Apply English in a realistic practice activity connected to {focus}.",
                tasks=[
                    DraftTask(
                        title=f"Role-play an English conversation for: {focus[:70]}",
                        estimated_minutes=45,
                        completion_criteria=f"Complete a short English role-play for {focus}, speaking or writing both sides of the exchange.",
                    ),
                    DraftTask(
                        title="Review the English practice and repeat it more clearly",
                        estimated_minutes=30,
                        completion_criteria="Identify two English expressions to improve, repeat the conversation, and note what became clearer.",
                    ),
                ],
            ),
        ]
    elif is_ai_website:
        milestones = [
            DraftMilestone(
                title="Compare AI tools for building your website",
                description=f"{learner_context} Evaluate AI website-building tools against the website you want and your constraints.",
                tasks=[
                    DraftTask(
                        title="Compare three AI website-building tools for your website",
                        estimated_minutes=60,
                        completion_criteria=f"Compare three available AI website-building tools for {focus} on output quality, editing control, accessibility, cost, and export options; record evidence for each.",
                    ),
                    DraftTask(
                        title="Select an AI website-building tool using your comparison",
                        estimated_minutes=30,
                        completion_criteria="Choose one tool from the comparison, explain why it fits your needs and constraints, and list the first website feature to build.",
                    ),
                ],
            ),
            DraftMilestone(
                title="Build a small website with the selected AI tool",
                description=f"Use the selected AI website tool to create a small first version for {focus}; review generated content rather than accepting it blindly.",
                tasks=[
                    DraftTask(
                        title="Create a one-page website with the selected AI tool",
                        estimated_minutes=60,
                        completion_criteria=f"Publish or preview a one-page website for {focus} with a clear purpose, relevant content, and at least one working interaction or navigation link.",
                    ),
                    DraftTask(
                        title="Review and edit the AI-generated website content",
                        estimated_minutes=45,
                        completion_criteria="Check the website text and images for accuracy, remove unsupported claims, and make at least two edits that improve clarity or usefulness.",
                    ),
                ],
            ),
            DraftMilestone(
                title="Test and improve the website",
                description=f"{learner_context} Test the website as a visitor and improve it using observed issues.",
                tasks=[
                    DraftTask(
                        title="Test the website on mobile and desktop",
                        estimated_minutes=45,
                        completion_criteria="Check the website at mobile and desktop widths, test every visible link and interaction, and record any layout or usability issue.",
                    ),
                    DraftTask(
                        title="Improve the website by fixing the highest-priority issue",
                        estimated_minutes=45,
                        completion_criteria="Fix at least one issue found during testing and repeat the affected checks to confirm the improvement.",
                    ),
                ],
            ),
        ]
    else:
        milestones = [
            DraftMilestone(
                title=f"Research practical approaches to: {focus[:65]}",
                description=f"{learner_context} Clarify what success means for the specific goal and identify approaches that fit your preferences and constraints.",
                tasks=[
                    DraftTask(
                        title=f"Find and compare two approaches for: {focus[:70]}",
                        estimated_minutes=45,
                        completion_criteria=f"Find two credible approaches or resources directly related to {focus}, compare their usefulness for your current level and constraints, and record the source of each.",
                    ),
                    DraftTask(
                        title=f"Choose a first approach and define a checkable result for: {focus[:65]}",
                        estimated_minutes=45,
                        completion_criteria=f"Choose one approach for {focus}, define a result you can complete in one session, and list the materials or preparation required.",
                    ),
                ],
            ),
            DraftMilestone(
                title=f"Practice a real task related to: {focus[:65]}",
                description=f"{learner_context} Apply the chosen approach to a small, realistic task that moves the goal forward{style_hint}.",
                tasks=[
                    DraftTask(
                        title=f"Complete one guided practice task for: {focus[:70]}",
                        estimated_minutes=45,
                        completion_criteria=f"Complete one practical exercise or activity directly related to {focus}, save or record the result, and note one difficulty to address.",
                    ),
                    DraftTask(
                        title=f"Repeat the practice task with one improvement for: {focus[:65]}",
                        estimated_minutes=45,
                        completion_criteria=f"Repeat the activity for {focus} while applying one improvement, then compare the new result with the first attempt.",
                    ),
                ],
            ),
            DraftMilestone(
                title=f"Deliver and review progress on: {focus[:65]}",
                description=f"{learner_context} Produce a small, reviewable result for the goal and use feedback or explicit criteria to decide what to improve.",
                tasks=[
                    DraftTask(
                        title=f"Complete a small deliverable for: {focus[:70]}",
                        estimated_minutes=60,
                        completion_criteria=f"Complete a small deliverable or observable outcome for {focus} and check it against the result defined at the start.",
                    ),
                    DraftTask(
                        title=f"Review the result for: {focus[:65]} and plan the next improvement",
                        estimated_minutes=45,
                        completion_criteria=f"Review the result for {focus}, record one thing that worked and one unresolved gap, and identify a concrete next step.",
                    ),
                ],
            ),
        ]

    task_limit = min(6, max(2, available_minutes // 60))
    remaining = task_limit
    selected: list[DraftMilestone] = []
    for milestone in milestones:
        chosen_tasks = milestone.tasks[:remaining]
        if chosen_tasks:
            selected.append(milestone.model_copy(update={"tasks": chosen_tasks}))
            remaining -= len(chosen_tasks)
        if remaining == 0:
            break

    if task_limit == 2 and available_minutes < 90:
        for milestone in selected:
            milestone.tasks = [
                task.model_copy(update={"estimated_minutes": 30})
                for task in milestone.tasks
            ]

    return PlanDraft(milestones=selected)


def schedule_draft(
    draft: PlanDraft,
    *,
    start_date: date,
    deadline: date,
    weekly_available_hours: int,
    existing_tasks: list[tuple[date | None, int | None]] | None = None,
    sequence_start: int = 0,
) -> list[dict[str, Any]]:
    if deadline < start_date:
        raise ValueError("The goal deadline has passed")

    day_count = (deadline - start_date).days + 1
    week_count = (day_count + 6) // 7
    weekly_capacity = weekly_available_hours * 60
    scheduled: list[dict[str, Any]] = []
    week_index = 0
    minutes_in_week = 0
    occupied_minutes = [0] * week_count
    for scheduled_date, estimated_minutes in existing_tasks or []:
        if scheduled_date is None or estimated_minutes is None:
            continue
        if start_date <= scheduled_date <= deadline:
            occupied_week = (scheduled_date - start_date).days // 7
            occupied_minutes[occupied_week] += estimated_minutes
    for sequence, milestone in enumerate(
        draft.milestones,
        start=sequence_start + 1,
    ):
        milestone_tasks = []
        last_task_date = start_date
        for task in milestone.tasks:
            if task.estimated_minutes > weekly_capacity:
                raise ValueError("A task exceeds the available hours for one week")
            if (
                minutes_in_week + occupied_minutes[week_index] + task.estimated_minutes
                > weekly_capacity
            ):
                week_index += 1
                minutes_in_week = 0
                while (
                    week_index < week_count
                    and occupied_minutes[week_index] + task.estimated_minutes
                    > weekly_capacity
                ):
                    week_index += 1
            if week_index >= week_count:
                raise ValueError("The plan exceeds the available time before the deadline")

            week_start = start_date + timedelta(days=week_index * 7)
            week_end = min(week_start + timedelta(days=6), deadline)
            day_offset = min(6, minutes_in_week // 60)
            task_date = min(week_start + timedelta(days=day_offset), week_end)
            if task_date > deadline:
                raise ValueError("A task cannot be scheduled before the goal deadline")
            milestone_tasks.append(
                {
                    "title": task.title,
                    "estimated_minutes": task.estimated_minutes,
                    "completion_criteria": task.completion_criteria,
                    "scheduled_date": task_date,
                    "deadline": deadline,
                }
            )
            last_task_date = task_date
            minutes_in_week += task.estimated_minutes

        scheduled.append(
            {
                "title": milestone.title,
                "description": milestone.description,
                "sequence": sequence,
                "target_date": last_task_date,
                "tasks": milestone_tasks,
            }
        )
    return scheduled


def build_scheduled_plan(
    goal: Goal,
    *,
    today: date | None = None,
    existing_tasks: list[tuple[date | None, int | None]] | None = None,
    sequence_start: int = 0,
) -> tuple[str, list[dict[str, Any]]]:
    start_date = today or date.today()
    if goal.deadline is None:
        raise ValueError("Set a target deadline before generating an action plan")
    if goal.deadline < start_date:
        raise ValueError("Choose a target deadline that is today or later")

    week_count = ((goal.deadline - start_date).days + 7) // 7
    weekly_capacity = goal.weekly_available_hours * 60
    occupied_minutes = [0] * week_count
    for scheduled_date, estimated_minutes in existing_tasks or []:
        if scheduled_date is not None and estimated_minutes is not None:
            if start_date <= scheduled_date <= goal.deadline:
                week_index = (scheduled_date - start_date).days // 7
                occupied_minutes[week_index] += estimated_minutes
    available_minutes = sum(
        max(0, weekly_capacity - minutes) for minutes in occupied_minutes
    )
    draft = build_fallback_draft(goal, available_minutes)
    scheduled = schedule_draft(
        draft,
        start_date=start_date,
        deadline=goal.deadline,
        weekly_available_hours=goal.weekly_available_hours,
        existing_tasks=existing_tasks,
        sequence_start=sequence_start,
    )
    return "fallback", scheduled

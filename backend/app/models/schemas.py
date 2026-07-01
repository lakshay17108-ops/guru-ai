from pydantic import BaseModel, Field


class Resource(BaseModel):
    """A single learning resource (article, video, documentation, etc.)."""
    resource_title: str = Field(..., min_length=1, description="Title of the resource")
    url: str = Field(..., min_length=1, description="URL to the resource")


class MilestoneProject(BaseModel):
    """A hands-on project associated with a milestone."""
    project_title: str = Field(..., min_length=1, description="Title of the project")
    description: str = Field(..., min_length=1, description="What the learner should build or do")


class Milestone(BaseModel):
    """A single milestone within a learning phase."""
    milestone_id: str = Field(..., min_length=1, description="Unique ID e.g. 'P1_M1'")
    title: str = Field(..., min_length=1, description="Milestone title")
    objectives: list[str] = Field(..., min_length=1, description="Learning objectives")
    suggested_queries: list[str] = Field(
        ..., min_length=1, description="Search queries the learner can use"
    )
    resources: list[Resource] = Field(..., min_length=1, description="Curated resources")
    milestone_project: MilestoneProject = Field(..., description="Hands-on project for this milestone")


class Phase(BaseModel):
    """A phase (week/unit) in the learning path."""
    phase: int = Field(..., ge=1, description="Phase number (1-indexed)")
    phase_title: str = Field(..., min_length=1, description="Title of the phase")
    milestones: list[Milestone] = Field(..., min_length=1, description="Milestones in this phase")


class LearningPath(BaseModel):
    """
    Top-level schema for a complete learning path.

    This is the *contract* between the LLM output and the frontend.
    Every response from /api/generate-path MUST validate against this model
    before being sent to the client.
    """
    topic: str = Field(..., min_length=1, description="The learning topic")
    estimated_time: str = Field(..., min_length=1, description="e.g. '8 weeks'")
    difficulty: str = Field(..., min_length=1, description="beginner / intermediate / advanced")
    curriculum: list[Phase] = Field(..., min_length=1, description="Ordered list of phases")

"""JSON shapes shared by server, client and session bundles (docs/SPEC.md sections 4 and 5).

This module is the source of truth. `client/src/shared/types.ts` is generated from it with
`make types` (scripts/gen_types.py); `tests/test_types_sync.py` fails if the two drift.

Conventions:
- Client times (`t`, `received`, `applied`, `painted`, `ended`, ...) are `performance.now()` ms
  on the one client clock. Server times are ISO strings and used for audit only.
- Literal aliases below become named TypeScript union types.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Literal aliases (exported to TypeScript by name)
# ---------------------------------------------------------------------------

Family = Literal["optical", "motion", "capture", "content", "physiology"]
CheckStatus = Literal["pass", "fail", "abstain"]
ThresholdSource = Literal["profile", "channel", "bootstrap", "rule"]
Route = Literal["PASS", "ADD_CHECKS", "AGENT_CHALLENGE", "ASSISTED_KYC", "HOLD"]
Unit = Literal["capture", "content_clip", "physiology", "light", "lens", "tilt", "hand"]
Threat = Literal["replay", "premade", "liveswap", "emulator"]
SessionMode = Literal["live", "superset"]
Product = Literal["instant_loan", "savings_account"]
ClockSource = Literal["captureTime", "rvfc_now", "raf"]
GyroPermission = Literal["granted", "denied", "not_needed"]
LightCondition = Literal["normal", "dim"]
LabelKind = Literal["genuine", "attack"]
EvalSet = Literal["A", "B"]
PulseKind = Literal["light", "lens", "tilt", "hand"]
PulseSource = Literal["planner", "agent", "superset"]
PromptKind = Literal["coach", "tilt", "hand", "info"]
ApplicantState = Literal["continue", "retry", "assisted", "under_review"]
FireKind = Literal["light", "tilt"]
DecisionAction = Literal["approve", "escalate", "assisted"]


# ---------------------------------------------------------------------------
# Check results and decisions (SPEC 4.6)
# ---------------------------------------------------------------------------


class CheckResult(BaseModel):
    check_id: str  # e.g. "optical.light.delay"
    unit: str  # planning unit, e.g. "light"
    family: Family
    status: CheckStatus
    score: float | None  # higher = more suspicious
    threshold: float | None
    threshold_source: ThresholdSource | None
    quality: float = Field(ge=0.0, le=1.0)
    features: dict[str, float]
    reason: str  # plain language, shown to the agent
    evidence_frames: list[int] = []

    @classmethod
    def abstain(
        cls,
        check_id: str,
        unit: str,
        family: Family,
        reason: str,
        quality: float = 0.0,
        features: dict[str, float] | None = None,
    ) -> CheckResult:
        """Checks never throw on bad input: they return this instead (CLAUDE.md rule 2)."""
        return cls(
            check_id=check_id,
            unit=unit,
            family=family,
            status="abstain",
            score=None,
            threshold=None,
            threshold_source=None,
            quality=min(max(quality, 0.0), 1.0),
            features=features or {},
            reason=reason,
        )


class FamilyResult(BaseModel):
    family: Family
    status: CheckStatus
    checks: list[str]


class SessionDecision(BaseModel):
    route: Route
    coverage: dict[str, list[str]]  # threat -> families with a strong pass
    failed_families: list[str]
    reasons: list[str]
    needs_human: bool
    provisional_thresholds: bool


class SessionResults(BaseModel):
    """Content of results.json (SPEC 4.1)."""

    checks: list[CheckResult] = []
    families: list[FamilyResult] = []
    decision: SessionDecision | None = None


# ---------------------------------------------------------------------------
# Session bundle records (SPEC 4.2 to 4.5)
# ---------------------------------------------------------------------------


class ScreenInfo(BaseModel):
    w: int
    h: int
    dpr: float


class GyroInfo(BaseModel):
    available: bool
    permission: GyroPermission


class ClientInfo(BaseModel):
    user_agent: str
    ua_mobile: bool
    pointer_coarse: bool
    screen: ScreenInfo
    camera_label: str
    track_settings: dict[str, Any] = {}
    track_capabilities: dict[str, Any] = {}
    has_rvfc: bool
    clock_source: ClockSource
    gyro: GyroInfo
    webgl_renderer: str | None = None
    webdriver: bool = False
    # Applicant opted out of bright flashes (SPEC 6.1 step 7): planner skips light pulses.
    accessibility_route: bool = False


class ProbeResult(BaseModel):
    face_frac: float
    luma_mean: float
    blur_lapvar: float
    backlit: bool
    fps_measured: float
    coaching_rounds: int


class Plan(BaseModel):
    rounds: list[list[str]]
    route_hint: Route | None = None
    active_seconds: float = 0.0


class Label(BaseModel):
    """Filled only for recorder-mode sessions. Person codes are pseudonymous (P01...)."""

    person: str
    device: str
    light: LightCondition
    kind: LabelKind
    attack_tool: str | None = None
    consent_ref: str
    skin_tone_mst: int | None = Field(default=None, ge=1, le=10)  # self-reported, never inferred
    set: EvalSet


class SessionMeta(BaseModel):
    """Content of meta.json."""

    session_id: str
    created_server_iso: str
    mode: SessionMode
    product: Product
    client: ClientInfo
    probe: ProbeResult | None = None
    profile_claimed: str | None = None
    profile_measured: str | None = None
    plan: Plan | None = None
    label: Label | None = None


class FrameRecord(BaseModel):
    """One line of frames.jsonl. `t` is the canonical frame time (see ClientInfo.clock_source)."""

    i: int
    t: float
    capture_time: float | None = None
    presented_frames: int | None = None
    media_time: float | None = None
    w: int
    h: int
    file: str


class PulseRecord(BaseModel):
    """One line of pulses.jsonl (pulses and prompts)."""

    pulse_id: str
    kind: PulseKind
    source: PulseSource
    params: dict[str, Any] = {}
    released_server_iso: str | None = None
    received: float | None = None
    applied: float | None = None
    painted: float | None = None
    ended: float | None = None
    ok: bool = False
    error: str | None = None
    sig: str | None = None


class SensorSample(BaseModel):
    """One line of sensors.jsonl. rr = rotationRate [alpha, beta, gamma]; units vary by device."""

    t: float
    rr: list[float] | None = None
    acc: list[float] | None = None
    interval: float | None = None


# ---------------------------------------------------------------------------
# REST payloads (SPEC 5)
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    mode: SessionMode
    product: Product
    client: ClientInfo


class CreateSessionResponse(BaseModel):
    session_id: str
    ws_url: str


class ApplicantResponse(BaseModel):
    """Everything the applicant API returns. Never a score or check name (extra fields rejected)."""

    model_config = ConfigDict(extra="forbid")

    state: ApplicantState
    message: str


class ProbeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tips: list[str]
    state: ApplicantState


class ReceivedResponse(BaseModel):
    received: int


class FireRequest(BaseModel):
    kind: FireKind


class FireResponse(BaseModel):
    pulse_id: str


class DecisionRequest(BaseModel):
    action: DecisionAction
    note: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


# ---------------------------------------------------------------------------
# WebSocket messages (SPEC 5)
# ---------------------------------------------------------------------------


class PromptMessage(BaseModel):
    type: Literal["prompt"] = "prompt"
    kind: PromptKind
    text: str
    duration_ms: int
    prompt_id: str


class PulseMessage(BaseModel):
    type: Literal["pulse"] = "pulse"
    pulse_id: str
    kind: Literal["light", "lens"]
    params: dict[str, Any]
    expires_in_ms: int
    sig: str


class DoneMessage(BaseModel):
    type: Literal["done"] = "done"
    state: ApplicantState
    message: str


class PulseAck(BaseModel):
    type: Literal["pulse_ack"] = "pulse_ack"
    pulse_id: str
    received: float | None = None
    applied: float | None = None
    painted: float | None = None
    ended: float | None = None
    ok: bool
    error: str | None = None


class PromptAck(BaseModel):
    type: Literal["prompt_ack"] = "prompt_ack"
    prompt_id: str
    painted: float | None = None
    ended: float | None = None


class Heartbeat(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    t: float


class SessionUpdate(BaseModel):
    """Pushed on /ws/console at most twice a second per session."""

    type: Literal["session_update"] = "session_update"
    session_id: str
    state: str
    route: Route | None = None
    results_delta: list[CheckResult] = []
    snapshot_jpeg_b64: str | None = None


# Order here is the order in the generated TypeScript file.
EXPORTED_MODELS: list[type[BaseModel]] = [
    CheckResult,
    FamilyResult,
    SessionDecision,
    SessionResults,
    ScreenInfo,
    GyroInfo,
    ClientInfo,
    ProbeResult,
    Plan,
    Label,
    SessionMeta,
    FrameRecord,
    PulseRecord,
    SensorSample,
    CreateSessionRequest,
    CreateSessionResponse,
    ApplicantResponse,
    ProbeResponse,
    ReceivedResponse,
    FireRequest,
    FireResponse,
    DecisionRequest,
    HealthResponse,
    PromptMessage,
    PulseMessage,
    DoneMessage,
    PulseAck,
    PromptAck,
    Heartbeat,
    SessionUpdate,
]

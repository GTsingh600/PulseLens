// GENERATED FILE: do not edit by hand.
// Source: server/pulselens/models.py. Regenerate with `make types`.
// Client times are performance.now() ms on the one client clock (CLAUDE.md rule 1).

export type Family = "optical" | "motion" | "capture" | "content" | "physiology";
export type CheckStatus = "pass" | "fail" | "abstain";
export type ThresholdSource = "profile" | "channel" | "bootstrap" | "rule";
export type Route = "PASS" | "ADD_CHECKS" | "AGENT_CHALLENGE" | "ASSISTED_KYC" | "HOLD";
export type Unit = "capture" | "content_clip" | "physiology" | "light" | "lens" | "tilt" | "hand";
export type Threat = "replay" | "premade" | "liveswap" | "emulator";
export type SessionMode = "live" | "superset";
export type Product = "instant_loan" | "savings_account";
export type ClockSource = "captureTime" | "rvfc_now" | "raf";
export type GyroPermission = "granted" | "denied" | "not_needed";
export type LightCondition = "normal" | "dim";
export type LabelKind = "genuine" | "attack";
export type EvalSet = "A" | "B";
export type PulseKind = "light" | "lens" | "tilt" | "hand";
export type PulseSource = "planner" | "agent" | "superset";
export type PromptKind = "coach" | "tilt" | "hand" | "info";
export type ApplicantState = "continue" | "retry" | "assisted" | "under_review";
export type FireKind = "light" | "tilt";
export type DecisionAction = "approve" | "escalate" | "assisted";

export interface CheckResult {
  check_id: string;
  unit: string;
  family: Family;
  status: CheckStatus;
  score: number | null;
  threshold: number | null;
  threshold_source: ThresholdSource | null;
  quality: number;
  features: Record<string, number>;
  reason: string;
  evidence_frames?: number[];
}

export interface FamilyResult {
  family: Family;
  status: CheckStatus;
  checks: string[];
}

export interface SessionDecision {
  route: Route;
  coverage: Record<string, string[]>;
  failed_families: string[];
  reasons: string[];
  needs_human: boolean;
  provisional_thresholds: boolean;
}

/** Content of results.json (SPEC 4.1). */
export interface SessionResults {
  checks?: CheckResult[];
  families?: FamilyResult[];
  decision?: SessionDecision | null;
}

export interface ScreenInfo {
  w: number;
  h: number;
  dpr: number;
}

export interface GyroInfo {
  available: boolean;
  permission: GyroPermission;
}

export interface ClientInfo {
  user_agent: string;
  ua_mobile: boolean;
  pointer_coarse: boolean;
  screen: ScreenInfo;
  camera_label: string;
  track_settings?: Record<string, unknown>;
  track_capabilities?: Record<string, unknown>;
  has_rvfc: boolean;
  clock_source: ClockSource;
  gyro: GyroInfo;
  webgl_renderer?: string | null;
  webdriver?: boolean;
  accessibility_route?: boolean;
}

export interface ProbeResult {
  face_frac: number;
  luma_mean: number;
  blur_lapvar: number;
  backlit: boolean;
  fps_measured: number;
  coaching_rounds: number;
}

export interface Plan {
  rounds: string[][];
  route_hint?: Route | null;
  active_seconds?: number;
}

/** Filled only for recorder-mode sessions. Person codes are pseudonymous (P01...). */
export interface Label {
  person: string;
  device: string;
  light: LightCondition;
  kind: LabelKind;
  attack_tool?: string | null;
  consent_ref: string;
  skin_tone_mst?: number | null;
  set: EvalSet;
}

/** Content of meta.json. */
export interface SessionMeta {
  session_id: string;
  created_server_iso: string;
  mode: SessionMode;
  product: Product;
  client: ClientInfo;
  probe?: ProbeResult | null;
  profile_claimed?: string | null;
  profile_measured?: string | null;
  plan?: Plan | null;
  label?: Label | null;
}

/** One line of frames.jsonl. `t` is the canonical frame time (see ClientInfo.clock_source). */
export interface FrameRecord {
  i: number;
  t: number;
  capture_time?: number | null;
  presented_frames?: number | null;
  media_time?: number | null;
  w: number;
  h: number;
  file: string;
}

/** One line of pulses.jsonl (pulses and prompts). */
export interface PulseRecord {
  pulse_id: string;
  kind: PulseKind;
  source: PulseSource;
  params?: Record<string, unknown>;
  released_server_iso?: string | null;
  received?: number | null;
  applied?: number | null;
  painted?: number | null;
  ended?: number | null;
  ok?: boolean;
  error?: string | null;
  sig?: string | null;
}

/** One line of sensors.jsonl. rr = rotationRate [alpha, beta, gamma]; units vary by device. */
export interface SensorSample {
  t: number;
  rr?: number[] | null;
  acc?: number[] | null;
  interval?: number | null;
}

export interface CreateSessionRequest {
  mode: SessionMode;
  product: Product;
  client: ClientInfo;
}

export interface CreateSessionResponse {
  session_id: string;
  ws_url: string;
}

/** Everything the applicant API returns. Never a score or check name (extra fields rejected). */
export interface ApplicantResponse {
  state: ApplicantState;
  message: string;
}

export interface ProbeResponse {
  tips: string[];
  state: ApplicantState;
}

export interface ReceivedResponse {
  received: number;
}

export interface FireRequest {
  kind: FireKind;
}

export interface FireResponse {
  pulse_id: string;
}

export interface DecisionRequest {
  action: DecisionAction;
  note: string;
}

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}

export interface PromptMessage {
  type?: "prompt";
  kind: PromptKind;
  text: string;
  duration_ms: number;
  prompt_id: string;
}

export interface PulseMessage {
  type?: "pulse";
  pulse_id: string;
  kind: "light" | "lens";
  params: Record<string, unknown>;
  expires_in_ms: number;
  sig: string;
}

export interface DoneMessage {
  type?: "done";
  state: ApplicantState;
  message: string;
}

export interface PulseAck {
  type?: "pulse_ack";
  pulse_id: string;
  received?: number | null;
  applied?: number | null;
  painted?: number | null;
  ended?: number | null;
  ok: boolean;
  error?: string | null;
}

export interface PromptAck {
  type?: "prompt_ack";
  prompt_id: string;
  painted?: number | null;
  ended?: number | null;
}

export interface Heartbeat {
  type?: "heartbeat";
  t: number;
}

/** Pushed on /ws/console at most twice a second per session. */
export interface SessionUpdate {
  type?: "session_update";
  session_id: string;
  state: string;
  route?: Route | null;
  results_delta?: CheckResult[];
  snapshot_jpeg_b64?: string | null;
}

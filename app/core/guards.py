import json
import uuid
from typing import Optional

from fastapi import HTTPException, WebSocket


class GuardContext:
    def __init__(self, user: dict, job_id: Optional[str] = None):
        self.user = user
        self.user_id = user.get("user_id_internal") or user.get("user_id")
        self.plan = user.get("plan", "free")
        self.job_id = job_id


class Guards:
    def __init__(self, redis_client, supabase_client):
        self.redis = redis_client
        self.supabase = supabase_client

    async def authenticate_http(self, verify_auth_fn, authorization: str):
        return await verify_auth_fn(authorization)

    async def authenticate_ws(self, websocket: WebSocket, verify_auth_fn):
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008)
            raise RuntimeError("Missing token")
        return await verify_auth_fn(f"Bearer {token}")

    def assert_job_ownership(self, ctx: GuardContext):
        if not ctx.job_id:
            return

        job_raw = self.redis.get(f"job:{ctx.job_id}")
        if job_raw:
            job = json.loads(job_raw)
            if job.get("user_id") == ctx.user_id:
                return

        if self.supabase:
            res = (
                self.supabase.table("simulations")
                .select("user_id")
                .eq("job_id", ctx.job_id)
                .execute()
            )
            if res.data and res.data[0].get("user_id") == ctx.user_id:
                return

        raise HTTPException(status_code=403, detail="Access denied")

    async def handle_idempotency(
        self, ctx: GuardContext, reserve_fn, get_fn, key: Optional[str]
    ) -> str:
        if not key:
            return str(uuid.uuid4())

        temp_id = str(uuid.uuid4())
        is_new = await reserve_fn(ctx.user_id, key, temp_id)

        if not is_new:
            existing = await get_fn(ctx.user_id, key)
            return existing

        return temp_id

    async def enforce_limits(
        self,
        ctx: GuardContext,
        check_rate_limit_fn,
        get_weekly_usage_fn,
        check_concurrent_runs_fn,
        weekly_limit: int,
    ):
        if check_rate_limit_fn:
            check_rate_limit_fn(ctx.user_id)

        if get_weekly_usage_fn and ctx.plan == "free":
            used = await get_weekly_usage_fn(ctx.user_id)
            if used >= weekly_limit:
                raise HTTPException(
                    status_code=429, detail="Weekly simulation limit reached"
                )

        if check_concurrent_runs_fn and ctx.plan == "free":
            has_running = check_concurrent_runs_fn(ctx.user_id)
            if has_running:
                raise HTTPException(
                    status_code=409, detail="Only one concurrent simulation allowed"
                )


_guards = None


def init_guards(redis_client, supabase_client):
    global _guards
    _guards = Guards(redis_client, supabase_client)
    return _guards


def get_guards() -> Guards:
    return _guards

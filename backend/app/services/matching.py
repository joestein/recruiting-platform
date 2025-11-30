from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.candidate import Candidate
from ..models.job import Job

settings = get_settings()


@dataclass
class CandidateMatch:
    candidate: Candidate
    score: int
    reason: str
    strategy: str  # "naive" or "openai"


@dataclass
class JobMatch:
    job: Job
    score: int
    reason: str
    strategy: str


def _normalize_text(text: str | None) -> set[str]:
    if not text:
        return set()
    return {t.strip(".,!?:;()").lower() for t in text.split() if t.strip()}


def _collect_job_keywords(job: Job) -> set[str]:
    kws: set[str] = set()
    if job.title:
        kws |= _normalize_text(job.title)
    if job.required_skills:
        kws |= {s.lower() for s in job.required_skills or []}
    if job.nice_to_have_skills:
        kws |= {s.lower() for s in job.nice_to_have_skills or []}
    return kws


def _collect_candidate_keywords(candidate: Candidate) -> set[str]:
    kws: set[str] = set()
    if candidate.current_title:
        kws |= _normalize_text(candidate.current_title)
    if candidate.headline:
        kws |= _normalize_text(candidate.headline)
    if candidate.current_company:
        kws |= _normalize_text(candidate.current_company)
    return kws


def _compute_naive_score_and_reason(job: Job, candidate: Candidate) -> tuple[int, str]:
    job_keywords = _collect_job_keywords(job)
    cand_keywords = _collect_candidate_keywords(candidate)

    if not job_keywords or not cand_keywords:
        return 0, "Insufficient information to compute keyword overlap."

    overlap = job_keywords & cand_keywords
    if not overlap:
        return 0, "No obvious keyword overlap between job and candidate profile."

    ratio = len(overlap) / max(len(job_keywords), 1)
    score = int(ratio * 100)
    score = max(0, min(100, score))

    top_terms = ", ".join(sorted(list(overlap))[:5])
    reason = f"Keyword overlap on: {top_terms}."

    return score, reason


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / math.sqrt(na * nb)


def _build_job_text(job: Job) -> str:
    parts: list[str] = []
    if job.title:
        parts.append(job.title)
    if job.description:
        parts.append(job.description)
    if job.required_skills:
        parts.append("Required skills: " + ", ".join(job.required_skills))
    if job.nice_to_have_skills:
        parts.append("Nice to have: " + ", ".join(job.nice_to_have_skills))
    return " ".join(parts)


def _build_candidate_text(candidate: Candidate) -> str:
    parts: list[str] = []
    if candidate.full_name:
        parts.append(candidate.full_name)
    if candidate.current_title:
        parts.append(candidate.current_title)
    if candidate.headline:
        parts.append(candidate.headline)
    if candidate.current_company:
        parts.append(candidate.current_company)
    if candidate.location:
        parts.append(f"Location: {candidate.location}")
    return " ".join(parts)


def _rank_candidates_openai(
    *,
    db: Session,
    org_id: int,
    job_id: int,
    limit: int,
) -> list[CandidateMatch]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    job = db.query(Job).filter(Job.org_id == org_id, Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")

    candidates = db.query(Candidate).filter(Candidate.org_id == org_id).all()
    if not candidates:
        return []

    job_text = _build_job_text(job)
    cand_texts = [_build_candidate_text(c) for c in candidates]
    inputs = [job_text] + cand_texts

    resp = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=inputs,
    )

    vectors = [d.embedding for d in resp.data]
    job_vec = vectors[0]
    cand_vecs = vectors[1:]

    matches: list[CandidateMatch] = []
    for candidate, vec in zip(candidates, cand_vecs):
        sim = _cosine_sim(job_vec, vec)
        score = int(max(0.0, sim) * 100)
        if score <= 0:
            continue

        job_keywords = _collect_job_keywords(job)
        cand_keywords = _collect_candidate_keywords(candidate)
        overlap = job_keywords & cand_keywords
        if overlap:
            terms = ", ".join(sorted(list(overlap))[:5])
            reason = (
                f"High semantic similarity between job and profile. "
                f"Overlapping terms include: {terms}."
            )
        else:
            reason = (
                "High semantic similarity between job description and candidate profile "
                "based on titles, skills, and description."
            )

        matches.append(
            CandidateMatch(
                candidate=candidate,
                score=score,
                reason=reason,
                strategy="openai",
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:limit]


def _rank_jobs_openai(
    *,
    db: Session,
    org_id: int,
    candidate_id: int,
    limit: int,
) -> list[JobMatch]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    candidate = (
        db.query(Candidate)
        .filter(Candidate.org_id == org_id, Candidate.id == candidate_id)
        .first()
    )
    if not candidate:
        raise ValueError("Candidate not found")

    jobs = db.query(Job).filter(Job.org_id == org_id).all()
    if not jobs:
        return []

    cand_text = _build_candidate_text(candidate)
    job_texts = [_build_job_text(j) for j in jobs]
    inputs = [cand_text] + job_texts

    resp = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=inputs,
    )

    vectors = [d.embedding for d in resp.data]
    cand_vec = vectors[0]
    job_vecs = vectors[1:]

    matches: list[JobMatch] = []
    for job, vec in zip(jobs, job_vecs):
        sim = _cosine_sim(cand_vec, vec)
        score = int(max(0.0, sim) * 100)
        if score <= 0:
            continue

        job_keywords = _collect_job_keywords(job)
        cand_keywords = _collect_candidate_keywords(candidate)
        overlap = job_keywords & cand_keywords
        if overlap:
            terms = ", ".join(sorted(list(overlap))[:5])
            reason = (
                f"High semantic similarity between candidate and job. "
                f"Overlapping terms include: {terms}."
            )
        else:
            reason = (
                "High semantic similarity between candidate profile and job description "
                "based on titles, skills, and description."
            )

        matches.append(
            JobMatch(
                job=job,
                score=score,
                reason=reason,
                strategy="openai",
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:limit]


def rank_candidates_for_job(
    *,
    db: Session,
    org_id: int,
    job_id: int,
    limit: int = 20,
) -> list[CandidateMatch]:
    use_openai = bool(settings.MATCHING_USE_OPENAI and settings.OPENAI_API_KEY)

    if use_openai:
        try:
            return _rank_candidates_openai(
                db=db,
                org_id=org_id,
                job_id=job_id,
                limit=limit,
            )
        except Exception as e:
            print(f"[matching] OpenAI job->candidates failed, falling back to naive. Error: {e}")

    job = db.query(Job).filter(Job.org_id == org_id, Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")

    candidates = db.query(Candidate).filter(Candidate.org_id == org_id).all()
    matches: list[CandidateMatch] = []
    for candidate in candidates:
        score, reason = _compute_naive_score_and_reason(job, candidate)
        if score <= 0:
            continue
        matches.append(
            CandidateMatch(
                candidate=candidate,
                score=score,
                reason=reason,
                strategy="naive",
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:limit]


def rank_jobs_for_candidate(
    *,
    db: Session,
    org_id: int,
    candidate_id: int,
    limit: int = 20,
) -> list[JobMatch]:
    use_openai = bool(settings.MATCHING_USE_OPENAI and settings.OPENAI_API_KEY)

    if use_openai:
        try:
            return _rank_jobs_openai(
                db=db,
                org_id=org_id,
                candidate_id=candidate_id,
                limit=limit,
            )
        except Exception as e:
            print(f"[matching] OpenAI candidate->jobs failed, falling back to naive. Error: {e}")

    candidate = (
        db.query(Candidate)
        .filter(Candidate.org_id == org_id, Candidate.id == candidate_id)
        .first()
    )
    if not candidate:
        raise ValueError("Candidate not found")

    jobs = db.query(Job).filter(Job.org_id == org_id).all()
    matches: list[JobMatch] = []
    for job in jobs:
        score, reason = _compute_naive_score_and_reason(job, candidate)
        if score <= 0:
            continue
        matches.append(
            JobMatch(
                job=job,
                score=score,
                reason=reason,
                strategy="naive",
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:limit]

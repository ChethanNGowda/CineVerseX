import os

import requests


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class TMDBServiceError(Exception):
    pass


class TMDBConfigError(TMDBServiceError):
    pass


class TMDBUnauthorizedError(TMDBServiceError):
    pass


class TMDBUnavailableError(TMDBServiceError):
    pass


def _tmdb_auth():
    bearer_token = os.environ.get("TMDB_BEARER_TOKEN", "").strip()
    api_key = os.environ.get("TMDB_API_KEY", "").strip()

    if not bearer_token and not api_key:
        raise TMDBConfigError("TMDB API credentials are not configured.")

    headers = {"accept": "application/json"}
    params = {}

    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    else:
        params["api_key"] = api_key

    return headers, params


def _tmdb_get(path, params=None):
    headers, auth_params = _tmdb_auth()
    merged_params = dict(auth_params)

    if params:
        merged_params.update(params)

    try:
        response = requests.get(
            f"{TMDB_BASE_URL}{path}",
            headers=headers,
            params=merged_params,
            timeout=10,
        )
    except requests.RequestException as exc:
        raise TMDBUnavailableError(f"TMDB request failed: {exc}") from exc

    if response.status_code in {401, 403}:
        raise TMDBUnauthorizedError("Invalid TMDB API credentials.")

    if response.status_code >= 500:
        raise TMDBUnavailableError("TMDB is currently unavailable.")

    if response.status_code >= 400:
        raise TMDBServiceError(f"TMDB request failed with status {response.status_code}.")

    return response.json()


def _image_url(path):
    if not path:
        return ""
    return f"{TMDB_IMAGE_BASE_URL}{path}"


def normalize_movie_details(payload):
    genres = [genre.get("name", "") for genre in payload.get("genres", []) if genre.get("name")]

    spoken_languages = payload.get("spoken_languages", []) or []
    language = ""

    for item in spoken_languages:
        language_name = item.get("english_name") or item.get("name")
        if language_name:
            language = language_name
            break

    if not language:
        language = (payload.get("original_language") or "").upper()

    return {
        "tmdb_id": payload.get("id"),
        "title": payload.get("title") or payload.get("original_title") or "",
        "description": payload.get("overview") or "",
        "poster": _image_url(payload.get("poster_path")),
        "backdrop": _image_url(payload.get("backdrop_path")),
        "genres": genres,
        "release_date": payload.get("release_date") or "",
        "runtime": payload.get("runtime") or 0,
        "language": language,
        "rating": round(float(payload.get("vote_average") or 0), 1),
    }


def fetch_movie_details_by_id(tmdb_id, language="en-US"):
    payload = _tmdb_get(
        f"/movie/{int(tmdb_id)}",
        {"language": language},
    )
    return normalize_movie_details(payload)


def search_best_movie_details(query, language="en-US"):
    search_payload = _tmdb_get(
        "/search/movie",
        {
            "query": query,
            "include_adult": "false",
            "language": language,
            "page": 1,
        },
    )

    results = search_payload.get("results") or []
    if not results:
        return {}

    best_result = results[0]
    return fetch_movie_details_by_id(best_result.get("id"), language=language)
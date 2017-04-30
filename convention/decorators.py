import hashlib

import flask
import wrapt


def add_cache_control(*directives):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        response = flask.make_response(wrapped(*args, **kwargs))
        response.headers["Cache-Control"] = ", ".join(directives) or "no-cache, no-store, max-age=0"
        return response
    return wrapper


def add_collection_controls(expand_endpoint, endpoint_ident_name, max_per_page=10):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        page = flask.request.args.get("page", 1, type=int)
        per_page = min(flask.request.args.get("per_page", max_per_page, type=int), max_per_page)
        paginator = wrapped(*args, **kwargs).paginate(page, per_page)
        expand = flask.request.args.get("expand")
        return {
            "items": [item.get_data() for item in paginator.items] if expand else [flask.url_for(expand_endpoint, endpoint_ident_name=item.key,
                                                                                                 _external=True) for item in paginator.items],
            "metadata": {
                "page": page,
                "per_page": per_page,
                "total_pages": paginator.pages,
                "first_page_url": flask.url_for(flask.request.endpoint, page=1, per_page=per_page, expand=expand, _external=True, **kwargs),
                "previous_page_url": flask.url_for(flask.request.endpoint, page=paginator.prev_num, per_page=per_page, expand=expand, _external=True,
                                                   **kwargs) if paginator.has_prev else None,
                "next_page_url": flask.url_for(flask.request.endpoint, page=paginator.next_num, per_page=per_page, expand=expand, _external=True,
                                               **kwargs) if paginator.has_next else None,
                "last_page_url": flask.url_for(flask.request.endpoint, page=paginator.pages, per_page=per_page, expand=expand, _external=True,
                                               **kwargs),
                "total_items": paginator.total,
            }
        }
    return wrapper


@wrapt.decorator
def add_etag(wrapped, instance, args, kwargs):
    response = flask.make_response(wrapped(*args, **kwargs))
    etag = '"%s"' % hashlib.md5(response.get_data()).hexdigest()
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=86400"
    if_match = flask.request.headers.get("If-Match")
    if_none_match = flask.request.headers.get("If-None-Match")
    if if_match is not None and if_match != "*" and etag not in (tag.strip() for tag in if_match.split(",")):
        flask.abort(412)
    elif if_none_match is not None and (if_none_match == "*" or etag in (tag.strip() for tag in if_none_match.split(", "))):
        flask.abort(304)
    return response


@wrapt.decorator
def to_json(wrapped, instance, args, kwargs):
    return_value = wrapped(*args, **kwargs)
    status = None
    headers = None
    if isinstance(return_value, tuple):
        if len(return_value) == 3:
            return_value, status, headers = return_value
        elif len(return_value) == 2:
            return_value, headers = return_value
    elif return_value is None:
        return_value = {}
    response = flask.jsonify(return_value)
    if status is not None:
        response.status_code = int(status)
    if headers is not None:
        response.headers.extend(headers)
    return response

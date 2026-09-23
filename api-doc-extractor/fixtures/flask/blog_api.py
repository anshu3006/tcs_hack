"""A small blog API used as a fixture for the extraction pipeline."""

from flask import Flask, jsonify, request

app = Flask(__name__)

POSTS = {}
NEXT_ID = 1


@app.route("/posts", methods=["GET"])
def list_posts():
    """List all blog posts.

    Supports optional filtering by author via a query string.
    """
    author = request.args.get("author")
    results = list(POSTS.values())
    if author:
        results = [p for p in results if p["author"] == author]
    return jsonify(results)


@app.route("/posts", methods=["POST"])
def create_post():
    """Create a new blog post.

    Expects a JSON body with 'title', 'body', and 'author' fields.
    """
    global NEXT_ID
    data = request.get_json()
    post = {"id": NEXT_ID, "title": data["title"], "body": data["body"], "author": data["author"]}
    POSTS[NEXT_ID] = post
    NEXT_ID += 1
    return jsonify(post), 201


@app.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    """Retrieve a single post by its numeric ID."""
    post = POSTS.get(post_id)
    if not post:
        return jsonify({"error": "not found"}), 404
    return jsonify(post)


@app.route("/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    """Update an existing post's title and/or body."""
    post = POSTS.get(post_id)
    if not post:
        return jsonify({"error": "not found"}), 404
    data = request.get_json()
    post.update({k: v for k, v in data.items() if k in ("title", "body")})
    return jsonify(post)


@app.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete a post by ID."""
    POSTS.pop(post_id, None)
    return "", 204


@app.route("/authors/<string:author_name>/posts", methods=["GET"])
def posts_by_author(author_name):
    """List every post written by a given author, with pagination."""
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    results = [p for p in POSTS.values() if p["author"] == author_name]
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)

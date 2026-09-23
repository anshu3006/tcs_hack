/**
 * Sample API code snippets for quick demos
 */

const SAMPLES = {
  flask: {
    name: 'Flask API',
    language: 'python',
    code: `from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory database
users = []
next_id = 1

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with optional filtering"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    return jsonify({
        'users': users[(page-1)*limit : page*limit],
        'total': len(users),
        'page': page
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID"""
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    global next_id
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'error': 'Name and email are required'}), 400
    
    user = {
        'id': next_id,
        'name': data['name'],
        'email': data['email'],
        'age': data.get('age'),
        'role': data.get('role', 'user')
    }
    next_id += 1
    users.append(user)
    return jsonify(user), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user"""
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    user.update({k: v for k, v in data.items() if k != 'id'})
    return jsonify(user)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    global users
    users = [u for u in users if u['id'] != user_id]
    return '', 204

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'user-api'})

if __name__ == '__main__':
    app.run(debug=True)`
  },

  express: {
    name: 'Express.js REST API',
    language: 'javascript',
    code: `const express = require('express');
const router = express.Router();

// Products API
const products = [];

router.get('/api/products', (req, res) => {
  const { category, minPrice, maxPrice, sort } = req.query;
  let filtered = [...products];
  
  if (category) filtered = filtered.filter(p => p.category === category);
  if (minPrice) filtered = filtered.filter(p => p.price >= Number(minPrice));
  if (maxPrice) filtered = filtered.filter(p => p.price <= Number(maxPrice));
  if (sort === 'price') filtered.sort((a, b) => a.price - b.price);
  
  res.json({ products: filtered, count: filtered.length });
});

router.get('/api/products/:id', (req, res) => {
  const product = products.find(p => p.id === req.params.id);
  if (!product) return res.status(404).json({ error: 'Product not found' });
  res.json(product);
});

router.post('/api/products', (req, res) => {
  const { name, price, category, description, stock } = req.body;
  if (!name || !price) {
    return res.status(400).json({ error: 'Name and price are required' });
  }
  const product = {
    id: Date.now().toString(),
    name, price, category,
    description: description || '',
    stock: stock || 0,
    createdAt: new Date().toISOString()
  };
  products.push(product);
  res.status(201).json(product);
});

router.put('/api/products/:id', (req, res) => {
  const index = products.findIndex(p => p.id === req.params.id);
  if (index === -1) return res.status(404).json({ error: 'Product not found' });
  products[index] = { ...products[index], ...req.body, id: req.params.id };
  res.json(products[index]);
});

router.delete('/api/products/:id', (req, res) => {
  const index = products.findIndex(p => p.id === req.params.id);
  if (index === -1) return res.status(404).json({ error: 'Product not found' });
  products.splice(index, 1);
  res.status(204).send();
});

router.post('/api/products/:id/reviews', (req, res) => {
  const product = products.find(p => p.id === req.params.id);
  if (!product) return res.status(404).json({ error: 'Product not found' });
  
  const review = {
    id: Date.now().toString(),
    rating: req.body.rating,
    comment: req.body.comment,
    author: req.body.author,
    createdAt: new Date().toISOString()
  };
  
  if (!product.reviews) product.reviews = [];
  product.reviews.push(review);
  res.status(201).json(review);
});

module.exports = router;`
  },

  fastapi: {
    name: 'FastAPI',
    language: 'python',
    code: `from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Task Management API")

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assignee: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None

tasks = []

@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List all tasks with optional filtering and pagination"""
    filtered = tasks
    if status:
        filtered = [t for t in filtered if t['status'] == status]
    if priority:
        filtered = [t for t in filtered if t['priority'] == priority]
    
    start = (page - 1) * limit
    return {
        "tasks": filtered[start:start + limit],
        "total": len(filtered),
        "page": page,
        "pages": (len(filtered) + limit - 1) // limit
    }

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a specific task by its ID"""
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    """Create a new task"""
    new_task = {
        "id": len(tasks) + 1,
        **task.dict(),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    tasks.append(new_task)
    return new_task

@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: int, updates: TaskUpdate):
    """Partially update a task"""
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = updates.dict(exclude_unset=True)
    task.update(update_data)
    task['updated_at'] = datetime.now().isoformat()
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task permanently"""
    global tasks
    tasks = [t for t in tasks if t['id'] != task_id]
    return {"message": "Task deleted successfully"}`
  },

  openapi: {
    name: 'OpenAPI JSON',
    language: 'json',
    code: JSON.stringify({
      "openapi": "3.0.0",
      "info": {
        "title": "Blog API",
        "version": "1.0.0"
      },
      "paths": {
        "/api/posts": {
          "get": {
            "summary": "List all blog posts",
            "operationId": "listPosts",
            "parameters": [
              { "name": "page", "in": "query", "schema": { "type": "integer" }, "description": "Page number" },
              { "name": "tag", "in": "query", "schema": { "type": "string" }, "description": "Filter by tag" }
            ],
            "responses": {
              "200": { "description": "List of posts" }
            }
          },
          "post": {
            "summary": "Create a new blog post",
            "operationId": "createPost",
            "requestBody": {
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "title": { "type": "string" },
                      "content": { "type": "string" },
                      "tags": { "type": "array", "items": { "type": "string" } },
                      "published": { "type": "boolean" }
                    },
                    "required": ["title", "content"]
                  }
                }
              }
            },
            "responses": {
              "201": { "description": "Post created" },
              "400": { "description": "Invalid input" }
            }
          }
        },
        "/api/posts/{postId}": {
          "get": {
            "summary": "Get a specific post",
            "operationId": "getPost",
            "parameters": [
              { "name": "postId", "in": "path", "required": true, "schema": { "type": "string" }, "description": "Post ID" }
            ],
            "responses": {
              "200": { "description": "Post details" },
              "404": { "description": "Post not found" }
            }
          },
          "put": {
            "summary": "Update a post",
            "operationId": "updatePost",
            "parameters": [
              { "name": "postId", "in": "path", "required": true, "schema": { "type": "string" } }
            ],
            "responses": {
              "200": { "description": "Post updated" },
              "404": { "description": "Post not found" }
            }
          },
          "delete": {
            "summary": "Delete a post",
            "operationId": "deletePost",
            "parameters": [
              { "name": "postId", "in": "path", "required": true, "schema": { "type": "string" } }
            ],
            "responses": {
              "204": { "description": "Post deleted" }
            }
          }
        },
        "/api/posts/{postId}/comments": {
          "get": {
            "summary": "Get comments for a post",
            "operationId": "getComments",
            "parameters": [
              { "name": "postId", "in": "path", "required": true, "schema": { "type": "string" } }
            ],
            "responses": {
              "200": { "description": "List of comments" }
            }
          },
          "post": {
            "summary": "Add a comment to a post",
            "operationId": "addComment",
            "parameters": [
              { "name": "postId", "in": "path", "required": true, "schema": { "type": "string" } }
            ],
            "responses": {
              "201": { "description": "Comment added" }
            }
          }
        }
      }
    }, null, 2)
  },

  spring: {
    name: 'Spring Boot',
    language: 'java',
    code: `@RestController
@RequestMapping("/api")
public class OrderController {

    @GetMapping("/orders")
    public ResponseEntity<List<Order>> getAllOrders(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<Order> orders = orderService.findAll(status, page, size);
        return ResponseEntity.ok(orders);
    }

    @GetMapping("/orders/{orderId}")
    public ResponseEntity<Order> getOrder(@PathVariable Long orderId) {
        Order order = orderService.findById(orderId);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    @PostMapping("/orders")
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest request) {
        Order order = orderService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @PutMapping("/orders/{orderId}")
    public ResponseEntity<Order> updateOrder(
            @PathVariable Long orderId,
            @RequestBody OrderRequest request) {
        Order order = orderService.update(orderId, request);
        return ResponseEntity.ok(order);
    }

    @DeleteMapping("/orders/{orderId}")
    public ResponseEntity<Void> deleteOrder(@PathVariable Long orderId) {
        orderService.delete(orderId);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/orders/{orderId}/status")
    public ResponseEntity<Order> updateOrderStatus(
            @PathVariable Long orderId,
            @RequestBody StatusUpdateRequest request) {
        Order order = orderService.updateStatus(orderId, request.getStatus());
        return ResponseEntity.ok(order);
    }
}`
  },

  go: {
    name: 'Go / Gin',
    language: 'go',
    code: `package main

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()

    // Book API routes
    r.GET("/api/books", listBooks)
    r.GET("/api/books/:id", getBook)
    r.POST("/api/books", createBook)
    r.PUT("/api/books/:id", updateBook)
    r.DELETE("/api/books/:id", deleteBook)
    r.GET("/api/books/search", searchBooks)

    r.Run(":8080")
}

func listBooks(c *gin.Context) {
    page := c.DefaultQuery("page", "1")
    limit := c.DefaultQuery("limit", "10")
    genre := c.Query("genre")
    
    books := getFilteredBooks(page, limit, genre)
    c.JSON(http.StatusOK, gin.H{
        "books": books,
        "total": len(books),
    })
}

func getBook(c *gin.Context) {
    id := c.Param("id")
    book, err := findBookById(id)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Book not found"})
        return
    }
    c.JSON(http.StatusOK, book)
}

func createBook(c *gin.Context) {
    var book Book
    if err := c.ShouldBindJSON(&book); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    created := saveBook(book)
    c.JSON(http.StatusCreated, created)
}

func updateBook(c *gin.Context) {
    id := c.Param("id")
    var book Book
    if err := c.ShouldBindJSON(&book); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    updated, err := updateBookById(id, book)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Book not found"})
        return
    }
    c.JSON(http.StatusOK, updated)
}

func deleteBook(c *gin.Context) {
    id := c.Param("id")
    if err := deleteBookById(id); err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Book not found"})
        return
    }
    c.Status(http.StatusNoContent)
}

func searchBooks(c *gin.Context) {
    query := c.Query("q")
    author := c.Query("author")
    results := search(query, author)
    c.JSON(http.StatusOK, gin.H{"results": results, "count": len(results)})
}`
  }
};

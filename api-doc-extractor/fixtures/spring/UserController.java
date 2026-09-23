package com.example.demo.controller;

import com.example.demo.model.User;
import com.example.demo.service.UserService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * List all registered users.
     * Supports optional pagination via the 'page' query parameter.
     */
    @GetMapping
    public List<User> listUsers(@RequestParam(required = false) Integer page) {
        return userService.findAll(page);
    }

    /**
     * Fetch a single user by their numeric ID.
     */
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }

    /**
     * Register a new user account.
     */
    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.create(user);
    }

    /**
     * Update an existing user's profile.
     */
    @PutMapping("/{id}")
    public User updateUser(@PathVariable Long id, @RequestBody User user) {
        return userService.update(id, user);
    }

    /**
     * Deactivate (soft-delete) a user account.
     */
    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.deactivate(id);
    }
}

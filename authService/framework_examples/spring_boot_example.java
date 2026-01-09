/**
 * Spring Boot Framework Example - AuthTemplate Pattern Implementation
 *
 * This example shows how to implement HTTP Basic Authentication
 * in a Spring Boot application using patterns similar to AuthTemplate.
 *
 * Dependencies (pom.xml):
 *   <dependency>
 *       <groupId>org.springframework.boot</groupId>
 *       <artifactId>spring-boot-starter-security</artifactId>
 *   </dependency>
 *   <dependency>
 *       <groupId>org.springframework.boot</groupId>
 *       <artifactId>spring-boot-starter-web</artifactId>
 *   </dependency>
 *   <dependency>
 *       <groupId>org.yaml</groupId>
 *       <artifactId>snakeyaml</artifactId>
 *   </dependency>
 */

package com.example.authtemplate;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.NoOpPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.*;
import java.time.LocalDateTime;
import java.util.stream.Collectors;

// ============================================================================
// Models
// ============================================================================

class AuthResult {
    public boolean success;
    public UserInfo user;
    public String message;
    public String errorCode;

    public AuthResult(boolean success, String message, String errorCode) {
        this.success = success;
        this.message = message;
        this.errorCode = errorCode;
    }

    public AuthResult(boolean success, UserInfo user, String message) {
        this.success = success;
        this.user = user;
        this.message = message;
    }
}

class UserInfo {
    public String username;
    public String email;
    public boolean isActive;
    public List<String> roles;
    public LocalDateTime lastLogin;

    public UserInfo(String username) {
        this.username = username;
        this.isActive = true;
        this.roles = new ArrayList<>(Arrays.asList("user"));
    }
}

class AuthRequest {
    public String username;
    public String password;

    public AuthRequest() {}
    public AuthRequest(String username, String password) {
        this.username = username;
        this.password = password;
    }
}

// ============================================================================
// Authentication Manager
// ============================================================================

@Configuration
class AuthConfig {
    /**
     * In-memory user details service with hardcoded users.
     * In production, load from database or external config.
     */
    @Bean
    public UserDetailsService userDetailsService() {
        // Create users (in production, load from YAML or database)
        UserDetails admin = User.builder()
                .username("admin")
                .password("admin_password")
                .roles("ADMIN", "USER")
                .build();

        UserDetails user1 = User.builder()
                .username("user1")
                .password("user1_password")
                .roles("USER")
                .build();

        UserDetails user2 = User.builder()
                .username("user2")
                .password("user2_password")
                .roles("USER")
                .build();

        return new InMemoryUserDetailsManager(admin, user1, user2);
    }

    /**
     * Password encoder - using NoOp for plaintext passwords
     * In production, use BCrypt or other secure encoders:
     *   return new BCryptPasswordEncoder();
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return NoOpPasswordEncoder.getInstance();
    }
}

// ============================================================================
// Security Configuration
// ============================================================================

@Configuration
@EnableWebSecurity
class SecurityConfig {
    /**
     * Configure HTTP security with Basic Authentication.
     */
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // Use HTTP Basic Authentication
                .httpBasic()
                .and()
                // Configure authorization rules
                .authorizeRequests()
                    .antMatchers("/health").permitAll()          // Public endpoint
                    .antMatchers("/protected/**").authenticated() // Protected endpoints
                    .antMatchers("/admin/**").hasRole("ADMIN")   // Admin endpoints
                    .anyRequest().authenticated()                // All others require auth
                .and()
                // Disable CSRF for this example
                .csrf().disable()
                // Use stateless sessions for REST API
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS);

        return http.build();
    }
}

// ============================================================================
// REST Controllers
// ============================================================================

@RestController
@RequestMapping("/")
class AuthExampleController {
    private static final Map<String, String> USERS = new HashMap<>(Map.of(
            "admin", "admin_password",
            "user1", "user1_password",
            "user2", "user2_password"
    ));

    /**
     * Health check endpoint (no authentication required).
     */
    @GetMapping("/health")
    public ResponseEntity<?> healthCheck() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "OK");
        response.put("service", "SpringBootAuth Example");
        return ResponseEntity.ok(response);
    }

    /**
     * Protected endpoint (requires authentication).
     */
    @GetMapping("/protected")
    public ResponseEntity<?> protectedEndpoint() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Map<String, Object> response = new HashMap<>();
        response.put("message", "You are authenticated");
        response.put("username", auth.getName());
        response.put("roles", auth.getAuthorities().stream()
                .map(a -> a.getAuthority())
                .collect(Collectors.toList()));

        return ResponseEntity.ok(response);
    }

    /**
     * Get information about the authenticated user.
     */
    @GetMapping("/user/info")
    public ResponseEntity<?> userInfo() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();

        UserInfo userInfo = new UserInfo(auth.getName());
        userInfo.lastLogin = LocalDateTime.now();

        Map<String, Object> response = new HashMap<>();
        response.put("user", userInfo);
        response.put("roles", auth.getAuthorities().stream()
                .map(a -> a.getAuthority())
                .collect(Collectors.toList()));

        return ResponseEntity.ok(response);
    }

    /**
     * Admin endpoint - list all users.
     */
    @GetMapping("/admin/users")
    public ResponseEntity<?> listUsers() {
        Map<String, Object> response = new HashMap<>();
        response.put("users", USERS.keySet());
        response.put("count", USERS.size());
        return ResponseEntity.ok(response);
    }

    /**
     * Test authentication with provided credentials.
     */
    @PostMapping("/auth/test")
    public ResponseEntity<?> authTest(@RequestBody AuthRequest request) {
        if (request.username == null || request.username.isEmpty() ||
            request.password == null || request.password.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Missing username or password"));
        }

        String storedPassword = USERS.get(request.username);
        if (storedPassword == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("success", false, "error", "User not found"));
        }

        if (!storedPassword.equals(request.password)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("success", false, "error", "Invalid credentials"));
        }

        UserInfo userInfo = new UserInfo(request.username);
        userInfo.lastLogin = LocalDateTime.now();

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("user", userInfo);

        return ResponseEntity.ok(response);
    }

    /**
     * Example error handler.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<?> handleException(Exception e) {
        Map<String, String> response = new HashMap<>();
        response.put("error", "Internal server error");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}

// ============================================================================
// Spring Boot Application
// ============================================================================

@SpringBootApplication
public class AuthTemplateApplication {
    public static void main(String[] args) {
        SpringApplication.run(AuthTemplateApplication.class, args);

        System.out.println("\nStarting Spring Boot Auth Example");
        System.out.println("Configured users: " + String.join(", ",
                "admin", "user1", "user2"));
        System.out.println("\nTest endpoints:");
        System.out.println("  GET  http://localhost:8080/health              (no auth)");
        System.out.println("  GET  http://localhost:8080/protected            (requires auth)");
        System.out.println("  POST http://localhost:8080/auth/test            (test auth)");
        System.out.println("  GET  http://localhost:8080/user/info            (requires auth)");
        System.out.println("  GET  http://localhost:8080/admin/users          (requires admin role)");
        System.out.println("\nExample credentials: admin / admin_password");
        System.out.println("");
    }
}

/*
 * Application Properties (application.properties):
 *
 * server.port=8080
 * server.servlet.context-path=/
 *
 * # Logging
 * logging.level.root=INFO
 * logging.level.org.springframework.security=DEBUG
 *
 * # Security
 * spring.security.user.name=admin
 * spring.security.user.password=password
 *
 * Example cURL commands:
 *
 * # Public endpoint
 * curl http://localhost:8080/health
 *
 * # Protected endpoint with basic auth
 * curl -u admin:admin_password http://localhost:8080/protected
 *
 * # Test auth
 * curl -X POST http://localhost:8080/auth/test \
 *   -H "Content-Type: application/json" \
 *   -d '{"username":"admin","password":"admin_password"}'
 */

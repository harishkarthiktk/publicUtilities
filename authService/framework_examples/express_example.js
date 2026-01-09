/**
 * Express.js Framework Example - AuthTemplate Pattern Implementation
 *
 * This example shows how to implement a similar authentication pattern
 * to AuthTemplate in an Express.js application.
 *
 * Dependencies:
 *   npm install express basic-auth yaml dotenv
 *
 * To run this example:
 *   node express_example.js
 */

const express = require('express');
const basicAuth = require('basic-auth');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// ============================================================================
// Authentication Module (Similar to AuthTemplate)
// ============================================================================

class AuthConfig {
    constructor(yamlFile = 'example_users.yaml', useEnv = true) {
        this.yamlFile = yamlFile;
        this.useEnv = useEnv;
        this.users = {};
        this.loadConfig();
    }

    loadConfig() {
        // Load from YAML
        if (fs.existsSync(this.yamlFile)) {
            try {
                const data = yaml.parse(fs.readFileSync(this.yamlFile, 'utf8'));
                this.users = data.users || data;
            } catch (e) {
                console.error(`Error loading YAML config: ${e.message}`);
            }
        }

        // Load from environment variables
        if (this.useEnv) {
            const envUser = process.env.AUTH_USER || process.env.BASIC_AUTH_USER;
            const envPassword = process.env.AUTH_PASSWORD || process.env.BASIC_AUTH_PASSWORD;

            if (envUser && envPassword) {
                this.users[envUser] = envPassword;
            }
        }
    }

    getUsers() {
        return { ...this.users };
    }

    getPassword(username) {
        return this.users[username] || null;
    }

    reload() {
        this.users = {};
        this.loadConfig();
    }
}

class AuthManager {
    constructor(config) {
        this.config = config;
        this.users = config.getUsers();
    }

    /**
     * Verify username and password
     * @param {string} username
     * @param {string} password
     * @param {string} ipAddress
     * @returns {object} Auth result
     */
    verifyCredentials(username, password, ipAddress = 'unknown') {
        if (!this.users[username]) {
            console.warn(`Auth attempt failed: user ${username} not found (IP: ${ipAddress})`);
            return {
                success: false,
                message: 'User not found',
                errorCode: 'USER_NOT_FOUND'
            };
        }

        if (this.users[username] !== password) {
            console.warn(`Auth attempt failed: invalid credentials for ${username} (IP: ${ipAddress})`);
            return {
                success: false,
                message: 'Invalid credentials',
                errorCode: 'INVALID_CREDENTIALS'
            };
        }

        console.info(`Auth successful for ${username} (IP: ${ipAddress})`);
        return {
            success: true,
            user: {
                username: username,
                isActive: true,
                roles: ['user'],
                lastLogin: new Date()
            },
            message: 'Authentication successful'
        };
    }

    listUsers() {
        return Object.keys(this.users);
    }

    getUserInfo(username) {
        return this.users[username] ? { username, exists: true } : null;
    }
}

// ============================================================================
// Express Application Setup
// ============================================================================

const app = express();
const authConfig = new AuthConfig('example_users.yaml');
const authManager = new AuthManager(authConfig);

app.use(express.json());

// Middleware to extract client IP
const getClientIp = (req) => {
    return req.ip || req.connection.remoteAddress || 'unknown';
};

// ============================================================================
// Authentication Middleware
// ============================================================================

/**
 * Middleware to require HTTP Basic Authentication
 *
 * Usage:
 *   app.get('/protected', requireAuth, (req, res) => {
 *       res.json({ message: 'Authenticated', user: req.user });
 *   });
 */
const requireAuth = (req, res, next) => {
    const credentials = basicAuth(req);
    const clientIp = getClientIp(req);

    if (!credentials) {
        res.statusCode = 401;
        res.setHeader('WWW-Authenticate', 'Basic realm="example"');
        return res.json({ error: 'Missing Authorization header' });
    }

    const result = authManager.verifyCredentials(
        credentials.name,
        credentials.pass,
        clientIp
    );

    if (!result.success) {
        res.statusCode = 401;
        return res.json({ error: result.message });
    }

    // Store authenticated user in request object
    req.user = result.user;
    req.clientIp = clientIp;

    next();
};

// ============================================================================
// Routes
// ============================================================================

/**
 * Health check endpoint (no authentication required)
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        service: 'ExpressAuth Example',
        timestamp: new Date().toISOString()
    });
});

/**
 * Protected endpoint (requires authentication)
 */
app.get('/protected', requireAuth, (req, res) => {
    res.json({
        message: 'You are authenticated',
        username: req.user.username,
        roles: req.user.roles
    });
});

/**
 * Get authenticated user information
 */
app.get('/user/info', requireAuth, (req, res) => {
    res.json({
        user: req.user,
        requestIp: req.clientIp
    });
});

/**
 * List all users (admin endpoint)
 */
app.get('/admin/users', requireAuth, (req, res) => {
    const users = authManager.listUsers();
    res.json({
        users: users,
        count: users.length
    });
});

/**
 * Test authentication with provided credentials
 *
 * POST body:
 *   {
 *       "username": "admin",
 *       "password": "password"
 *   }
 */
app.post('/auth/test', express.json(), (req, res) => {
    const { username, password } = req.body;
    const clientIp = getClientIp(req);

    if (!username || !password) {
        return res.status(400).json({ error: 'Missing username or password' });
    }

    const result = authManager.verifyCredentials(username, password, clientIp);

    if (result.success) {
        res.json({
            success: true,
            user: result.user
        });
    } else {
        res.status(401).json({
            success: false,
            error: result.message
        });
    }
});

// ============================================================================
// Error Handlers
// ============================================================================

app.use((req, res) => {
    res.status(404).json({ error: 'Not Found' });
});

app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// ============================================================================
// Server Startup
// ============================================================================

const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`\nStarting Express Auth Example`);
    console.log(`Configured users: ${authManager.listUsers().join(', ')}`);
    console.log(`\nTest endpoints:`);
    console.log(`  GET  http://localhost:${PORT}/health              (no auth)`);
    console.log(`  GET  http://localhost:${PORT}/protected            (requires auth)`);
    console.log(`  POST http://localhost:${PORT}/auth/test            (test auth)`);
    console.log(`  GET  http://localhost:${PORT}/user/info            (requires auth)`);
    console.log(`  GET  http://localhost:${PORT}/admin/users          (requires auth)`);
    console.log(`\nExample credentials: admin / password`);
    console.log(`\nServer running on http://localhost:${PORT}\n`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

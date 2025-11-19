<?php
/**
 * VidStream API Handler
 *
 * @package VidStream_Connector
 */

if (!defined('ABSPATH')) {
    exit;
}

class VidStream_API {
    
    /**
     * API URL
     */
    private $api_url;
    
    /**
     * Access token
     */
    private $access_token;
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->api_url = get_option('vidstream_api_url');
    }
    
    /**
     * Authenticate with VidStream
     */
    public function authenticate($username = null, $password = null) {
        if (!$username) {
            $username = get_option('vidstream_username');
        }
        if (!$password) {
            $password = get_option('vidstream_password');
        }
        
        $response = wp_remote_post($this->api_url . '/api/auth/login', array(
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode(array(
                'username' => $username,
                'password' => $password
            )),
            'timeout' => 15
        ));
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'message' => $response->get_error_message()
            );
        }
        
        $body = json_decode(wp_remote_retrieve_body($response), true);
        
        if (isset($body['access_token'])) {
            $this->access_token = $body['access_token'];
            update_option('vidstream_access_token', $this->access_token);
            update_option('vidstream_token_expires', time() + (7 * 24 * 60 * 60)); // 7 days
            
            return array(
                'success' => true,
                'token' => $this->access_token,
                'must_change_password' => isset($body['must_change_password']) ? $body['must_change_password'] : false
            );
        }
        
        return array(
            'success' => false,
            'message' => isset($body['detail']) ? $body['detail'] : 'Authentication failed'
        );
    }
    
    /**
     * Get access token
     */
    private function get_token() {
        if ($this->access_token) {
            return $this->access_token;
        }
        
        // Check if token exists and is valid
        $token = get_option('vidstream_access_token');
        $expires = get_option('vidstream_token_expires', 0);
        
        if ($token && $expires > time()) {
            $this->access_token = $token;
            return $token;
        }
        
        // Re-authenticate
        $auth = $this->authenticate();
        if ($auth['success']) {
            return $auth['token'];
        }
        
        return false;
    }
    
    /**
     * Make API request
     */
    private function request($endpoint, $method = 'GET', $data = null) {
        $token = $this->get_token();
        
        if (!$token) {
            return array(
                'success' => false,
                'message' => 'Not authenticated'
            );
        }
        
        $url = $this->api_url . $endpoint;
        $args = array(
            'method' => $method,
            'headers' => array(
                'Authorization' => 'Bearer ' . $token,
                'Content-Type' => 'application/json'
            ),
            'timeout' => 30
        );
        
        if ($data && in_array($method, array('POST', 'PATCH', 'PUT'))) {
            $args['body'] = json_encode($data);
        }
        
        $response = wp_remote_request($url, $args);
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'message' => $response->get_error_message()
            );
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $body = json_decode(wp_remote_retrieve_body($response), true);
        
        if ($status_code >= 200 && $status_code < 300) {
            return array(
                'success' => true,
                'data' => $body
            );
        }
        
        return array(
            'success' => false,
            'message' => isset($body['detail']) ? $body['detail'] : 'API request failed',
            'status_code' => $status_code
        );
    }
    
    /**
     * Get all videos
     */
    public function get_videos($folder_id = null) {
        $endpoint = '/api/videos';
        if ($folder_id) {
            $endpoint .= '?folder_id=' . $folder_id;
        }
        return $this->request($endpoint);
    }
    
    /**
     * Get single video
     */
    public function get_video($video_id) {
        return $this->request('/api/videos/' . $video_id);
    }
    
    /**
     * Get all folders
     */
    public function get_folders() {
        return $this->request('/api/folders');
    }
    
    /**
     * Get video thumbnail URL
     */
    public function get_thumbnail_url($video_id) {
        return $this->api_url . '/api/stream/thumbnail/' . $video_id;
    }
    
    /**
     * Get video stream URL (HLS)
     */
    public function get_stream_url($video_id) {
        return $this->api_url . '/api/stream/hls/' . $video_id . '/playlist.m3u8';
    }
    
    /**
     * Get embed settings
     */
    public function get_embed_settings($video_id) {
        return $this->request('/api/embed-settings/' . $video_id);
    }
    
    /**
     * Get embed code
     */
    public function get_embed_code($video_id) {
        return $this->request('/api/embed-code/' . $video_id);
    }
    
    /**
     * Test connection
     */
    public function test_connection() {
        $auth = $this->authenticate();
        
        if (!$auth['success']) {
            return $auth;
        }
        
        $videos = $this->get_videos();
        
        if ($videos['success']) {
            return array(
                'success' => true,
                'message' => 'Connection successful',
                'video_count' => is_array($videos['data']) ? count($videos['data']) : 0
            );
        }
        
        return $videos;
    }
    
    /**
     * Download thumbnail
     */
    public function download_thumbnail($video_id, $save_path) {
        $thumbnail_url = $this->get_thumbnail_url($video_id);
        
        $response = wp_remote_get($thumbnail_url, array(
            'timeout' => 30,
            'stream' => true,
            'filename' => $save_path
        ));
        
        if (is_wp_error($response)) {
            return false;
        }
        
        return wp_remote_retrieve_response_code($response) === 200;
    }
}

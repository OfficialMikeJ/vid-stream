/**
 * StreamLab Invites Frontend JavaScript
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        
        // Handle invite code verification
        $('#streamlab-invite-form').on('submit', function(e) {
            e.preventDefault();
            
            var $form = $(this);
            var $input = $('#invite-code');
            var $error = $('#invite-error');
            var $button = $form.find('button[type="submit"]');
            var $buttonText = $button.find('.button-text');
            var $buttonLoader = $button.find('.button-loader');
            var code = $input.val().trim();
            
            // Clear previous errors
            $error.hide().text('');
            
            // Validate
            if (!code) {
                $error.text(streamlabInvites.errors.empty_code).show();
                return;
            }
            
            // Disable button and show loader
            $button.prop('disabled', true);
            $buttonText.hide();
            $buttonLoader.show();
            
            // Verify code
            $.ajax({
                url: streamlabInvites.ajax_url,
                type: 'POST',
                data: {
                    action: 'streamlab_verify_code',
                    nonce: streamlabInvites.nonce,
                    code: code
                },
                success: function(response) {
                    if (response.success) {
                        // Code verified - redirect to registration
                        window.location.href = '/wp-login.php?action=register';
                    } else {
                        $error.text(response.message || streamlabInvites.errors.invalid_code).show();
                    }
                },
                error: function() {
                    $error.text('An error occurred. Please try again.').show();
                },
                complete: function() {
                    $button.prop('disabled', false);
                    $buttonText.show();
                    $buttonLoader.hide();
                }
            });
        });
        
        // Format invite code input
        $('#invite-code').on('input', function() {
            var value = $(this).val().toUpperCase().replace(/[^A-Z0-9]/g, '');
            
            // Add dashes for formatting
            if (value.length > 3) {
                value = value.slice(0, 3) + '-' + value.slice(3);
            }
            if (value.length > 7) {
                value = value.slice(0, 7) + '-' + value.slice(7);
            }
            
            $(this).val(value.slice(0, 11)); // Max length XXX-XXX-XXX
        });
        
    });
    
})(jQuery);
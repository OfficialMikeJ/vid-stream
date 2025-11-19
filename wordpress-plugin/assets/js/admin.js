/**
 * VidStream Connector Admin JavaScript
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        
        // Manual sync button
        $('#vidstream-sync-btn').on('click', function() {
            var $btn = $(this);
            var $progress = $('#vidstream-sync-progress');
            var $result = $('#vidstream-sync-result');
            var $progressFill = $('.vidstream-progress-fill');
            var $progressText = $('.vidstream-progress-text');
            
            // Disable button
            $btn.prop('disabled', true).text('Syncing...');
            
            // Show progress
            $progress.show();
            $result.hide();
            $progressFill.css('width', '0%');
            $progressText.text('Starting sync...');
            
            // Animate progress
            var progressInterval = setInterval(function() {
                var currentWidth = parseInt($progressFill.css('width'));
                var containerWidth = $progressFill.parent().width();
                var percentage = (currentWidth / containerWidth) * 100;
                
                if (percentage < 90) {
                    $progressFill.css('width', (percentage + 10) + '%');
                }
            }, 500);
            
            // Make AJAX request
            $.ajax({
                url: vidstreamAjax.ajax_url,
                type: 'POST',
                data: {
                    action: 'vidstream_manual_sync',
                    nonce: vidstreamAjax.nonce
                },
                success: function(response) {
                    clearInterval(progressInterval);
                    $progressFill.css('width', '100%');
                    
                    if (response.success) {
                        var data = response.data;
                        $progressText.text('Sync completed!');
                        
                        var message = '<div class="notice notice-success"><p><strong>Sync Completed Successfully!</strong></p>';
                        message += '<ul>';
                        message += '<li>Total Videos: ' + data.total + '</li>';
                        message += '<li>Synced: ' + data.synced + '</li>';
                        message += '<li>Failed: ' + data.failed + '</li>';
                        message += '<li>Skipped: ' + data.skipped + '</li>';
                        message += '</ul></div>';
                        
                        $result.html(message).show();
                        
                        // Reload after 2 seconds
                        setTimeout(function() {
                            location.reload();
                        }, 2000);
                    } else {
                        $progressText.text('Sync failed!');
                        $result.html('<div class="notice notice-error"><p>' + response.data.message + '</p></div>').show();
                    }
                },
                error: function(xhr, status, error) {
                    clearInterval(progressInterval);
                    $progressText.text('Sync failed!');
                    $result.html('<div class="notice notice-error"><p>An error occurred: ' + error + '</p></div>').show();
                },
                complete: function() {
                    $btn.prop('disabled', false).text('Sync All Videos Now');
                }
            });
        });
        
        // Auto-hide notices after 5 seconds
        setTimeout(function() {
            $('.notice.is-dismissible').fadeOut();
        }, 5000);
    });
    
})(jQuery);
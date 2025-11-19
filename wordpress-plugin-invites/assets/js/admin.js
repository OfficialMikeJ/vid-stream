/**
 * StreamLab Invites Admin JavaScript
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        
        // Generate invite code
        $('#generate-code-btn').on('click', function() {
            var $btn = $(this);
            var notes = $('#code-notes').val();
            
            $btn.prop('disabled', true).text('Generating...');
            
            $.ajax({
                url: streamlabInvites.ajax_url,
                type: 'POST',
                data: {
                    action: 'streamlab_generate_code',
                    nonce: streamlabInvites.nonce,
                    notes: notes
                },
                success: function(response) {
                    if (response.success) {
                        $('#generated-code-value').text(response.data.code);
                        $('#generated-code-display').slideDown();
                        $('#code-notes').val('');
                        
                        // Reload stats
                        setTimeout(function() {
                            location.reload();
                        }, 3000);
                    } else {
                        alert('Error: ' + (response.data.message || 'Failed to generate code'));
                    }
                },
                error: function() {
                    alert('An error occurred while generating the code.');
                },
                complete: function() {
                    $btn.prop('disabled', false).html('<span class="dashicons dashicons-plus-alt"></span> Generate Invite Code');
                }
            });
        });
        
        // Copy code to clipboard
        $('#copy-code-btn').on('click', function() {
            var code = $('#generated-code-value').text();
            var $btn = $(this);
            
            // Create temporary input
            var $temp = $('<input>');
            $('body').append($temp);
            $temp.val(code).select();
            document.execCommand('copy');
            $temp.remove();
            
            // Update button text
            var originalHtml = $btn.html();
            $btn.html('<span class="dashicons dashicons-yes"></span> Copied!');
            
            setTimeout(function() {
                $btn.html(originalHtml);
            }, 2000);
        });
        
        // Revoke code
        $('.revoke-code').on('click', function() {
            if (!confirm(streamlabInvites.confirm_revoke)) {
                return;
            }
            
            var $btn = $(this);
            var codeId = $btn.data('code-id');
            var $row = $btn.closest('tr');
            
            $btn.prop('disabled', true).text('Revoking...');
            
            $.ajax({
                url: streamlabInvites.ajax_url,
                type: 'POST',
                data: {
                    action: 'streamlab_revoke_code',
                    nonce: streamlabInvites.nonce,
                    id: codeId
                },
                success: function(response) {
                    if (response.success) {
                        $row.find('.status-badge')
                            .removeClass('status-active')
                            .addClass('status-revoked')
                            .text('Revoked');
                        $btn.remove();
                    } else {
                        alert('Error: ' + (response.data.message || 'Failed to revoke code'));
                        $btn.prop('disabled', false).text('Revoke');
                    }
                },
                error: function() {
                    alert('An error occurred while revoking the code.');
                    $btn.prop('disabled', false).text('Revoke');
                }
            });
        });
        
        // Delete code
        $('.delete-code').on('click', function() {
            if (!confirm(streamlabInvites.confirm_delete)) {
                return;
            }
            
            var $btn = $(this);
            var codeId = $btn.data('code-id');
            var $row = $btn.closest('tr');
            
            $btn.prop('disabled', true).text('Deleting...');
            
            $.ajax({
                url: streamlabInvites.ajax_url,
                type: 'POST',
                data: {
                    action: 'streamlab_delete_code',
                    nonce: streamlabInvites.nonce,
                    id: codeId
                },
                success: function(response) {
                    if (response.success) {
                        $row.fadeOut(function() {
                            $(this).remove();
                        });
                    } else {
                        alert('Error: ' + (response.data.message || 'Failed to delete code'));
                        $btn.prop('disabled', false).text('Delete');
                    }
                },
                error: function() {
                    alert('An error occurred while deleting the code.');
                    $btn.prop('disabled', false).text('Delete');
                }
            });
        });
        
    });
    
})(jQuery);
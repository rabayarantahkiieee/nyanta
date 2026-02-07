# Enhanced Broadcast Feature Documentation

## Overview

The enhanced broadcast feature provides a robust and reliable way to send messages to all bot users with advanced features including:

- **Batch Processing**: Processes users in batches for better performance
- **Concurrency Control**: Configurable concurrent message sending
- **Advanced Error Handling**: Comprehensive error detection and recovery
- **Retry Mechanism**: Automatic retry for failed messages
- **Detailed Logging**: Extensive logging for monitoring and debugging
- **Placeholder Support**: Personalized messages with user data
- **HTML Formatting**: Rich text formatting support
- **Media Support**: All media types supported

## Key Improvements

### 1. Batch Processing
- Users are processed in batches (default: 10 users per batch)
- Reduces memory usage and improves performance
- Configurable batch size

### 2. Concurrency Control
- Limits concurrent message sending (default: 5 concurrent tasks)
- Prevents rate limiting and API bans
- Configurable concurrency level

### 3. Advanced Error Handling
- Specific handling for different error types:
  - `FloodWait`: Automatic retry with exponential backoff
  - `UserIsBlocked`: Marks user as blocked and skips
  - `InputUserDeactivated`: Marks user as deleted and skips
  - General exceptions: Retry with exponential backoff

### 4. Retry Mechanism
- Automatic retry for failed messages (default: 3 attempts)
- Exponential backoff between retries
- Detailed logging of retry attempts

### 5. Detailed Logging
- Comprehensive logging at different levels:
  - Info: General progress and success messages
  - Warning: Recoverable issues and retries
  - Error: Critical failures and debugging info
- Log files for persistent storage:
  - `broadcast_logs.txt`: Activity logs
  - `broadcast_errors.txt`: Error details

## Configuration

### Environment Variables

```env
# Broadcast delay (seconds)
BROADCAST_DELAY=0.15  # With placeholders
BROADCAST_DELAY=0.05  # Without placeholders

# Batch processing
BROADCAST_BATCH_SIZE=10

# Concurrency control
BROADCAST_MAX_CONCURRENT=5

# Retry settings
BROADCAST_MAX_RETRIES=3
```

## Usage

### Basic Broadcast

```
/broadcast [reply to message]
```

### Supported Media Types

- Text messages
- Photos
- Videos
- Documents
- Audio files
- Voice messages
- Animations (GIFs)
- Stickers
- Video notes

### HTML Formatting

Supported HTML tags:
- `<b>` - Bold text
- `<i>` - Italic text
- `<blockquote>` - Block quotes
- `\n` - New lines

### Placeholder Variables

Personalize messages with user data:
- `{ID}` - User ID
- `{NAME}` - First name
- `{SURNAME}` - Last name
- `{NAMESURNAME}` - Full name
- `{USERNAME}` - Username
- `{MENTION}` - User mention
- `{DATE}` - Current date (DD/MM/YYYY)
- `{TIME}` - Current time (HH:MM:SS)
- `{WEEKDAY}` - Day name
- `{LANG}` - Language code

## Error Handling

### Common Errors and Solutions

1. **FloodWait Errors**:
   - Automatic retry with increasing wait times
   - Maximum 60 seconds wait time
   - Logged as warnings

2. **Blocked Users**:
   - Automatically detected and marked
   - Skipped in future broadcasts
   - Logged as warnings

3. **Deactivated Accounts**:
   - Automatically detected and marked
   - Skipped in future broadcasts
   - Logged as warnings

4. **General Errors**:
   - Retried up to 3 times
   - Exponential backoff between retries
   - Detailed error logging

## Monitoring and Logging

### Log Files

1. **broadcast_logs.txt**:
   - Contains broadcast activity records
   - Format: `[timestamp] BROADCAST | Admin: admin_id | Type: message_type | Total: total_users | Success: successful | Failed: failed | Blocked: blocked | Deleted: deleted | FloodWaits: flood_waits | Success Rate: success_rate%`

2. **broadcast_errors.txt**:
   - Contains detailed error information
   - Format: `[timestamp] BROADCAST_ERROR | ChatID: chat_id | Type: error_type | Message: error_message | Retries: retry_count`

### Console Output

- Real-time progress updates
- Success/failure statistics
- Error warnings and debugging info

## Performance Metrics

### Success Rate Calculation

```
Success Rate = (Successful Messages / Total Messages) * 100
```

### Broadcast Duration

- Tracked from start to finish
- Displayed in final report
- Used for performance monitoring

## Best Practices

1. **Testing**: Always test broadcasts with a small group first
2. **Monitoring**: Check log files regularly for issues
3. **Configuration**: Adjust batch size and concurrency based on server capacity
4. **Content**: Use placeholders for personalized messages
5. **Timing**: Schedule broadcasts during low-traffic periods

## Troubleshooting

### Common Issues

1. **Low Success Rate**:
   - Check for high number of blocked/deleted users
   - Review error logs for patterns
   - Adjust retry settings

2. **Slow Performance**:
   - Reduce batch size
   - Decrease concurrency
   - Increase delay between batches

3. **API Errors**:
   - Check Telegram API status
   - Review rate limiting settings
   - Monitor for FloodWait errors

## Technical Details

### Batch Processing Algorithm

1. Divide users into batches
2. Process each batch sequentially
3. Within each batch, process users concurrently (up to max_concurrent)
4. Apply rate limiting between batches

### Retry Mechanism

1. Initial attempt
2. If failed, wait with exponential backoff
3. Retry up to max_retries times
4. Log detailed error information

### Error Classification

- **Recoverable**: FloodWait, network issues (retry)
- **Permanent**: Blocked users, deactivated accounts (skip)
- **Critical**: Database errors, configuration issues (stop)

## Future Enhancements

1. **Broadcast Scheduling**: Schedule broadcasts for specific times
2. **User Segmentation**: Target specific user groups
3. **A/B Testing**: Test different message versions
4. **Analytics**: Detailed engagement metrics
5. **Web Interface**: Web-based broadcast management

## Support

For issues or questions, refer to:
- Error logs in `broadcast_errors.txt`
- Activity logs in `broadcast_logs.txt`
- Configuration settings in `.env` file
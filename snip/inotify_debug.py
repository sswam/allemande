async def follow_changes(self, f):
    """Follow the file, until it is removed"""
    removed_flags = aionotify.Flags.DELETE_SELF | aionotify.Flags.MOVE_SELF
    all_flags = aionotify.Flags.DELETE_SELF | aionotify.Flags.MOVE_SELF | aionotify.Flags.ACCESS | aionotify.Flags.ATTRIB | aionotify.Flags.CLOSE_WRITE | aionotify.Flags.CLOSE_NOWRITE | aionotify.Flags.CREATE | aionotify.Flags.DELETE | aionotify.Flags.MOVED_FROM | aionotify.Flags.MOVED_TO | aionotify.Flags.OPEN

    logger.debug("IN_ACCESS = %d", aionotify.Flags.ACCESS)
    logger.debug("IN_ATTRIB = %d", aionotify.Flags.ATTRIB)
    logger.debug("IN_CLOSE_WRITE = %d", aionotify.Flags.CLOSE_WRITE)
    logger.debug("IN_CLOSE_NOWRITE = %d", aionotify.Flags.CLOSE_NOWRITE)
    logger.debug("IN_CREATE = %d", aionotify.Flags.CREATE)
    logger.debug("IN_DELETE = %d", aionotify.Flags.DELETE)
    logger.debug("IN_DELETE_SELF = %d", aionotify.Flags.DELETE_SELF)
    logger.debug("IN_MODIFY = %d", aionotify.Flags.MODIFY)
    logger.debug("IN_MOVE_SELF = %d", aionotify.Flags.MOVE_SELF)
    logger.debug("IN_MOVED_FROM = %d", aionotify.Flags.MOVED_FROM)
    logger.debug("IN_MOVED_TO = %d", aionotify.Flags.MOVED_TO)
    logger.debug("IN_OPEN = %d", aionotify.Flags.OPEN)

    try:
        watcher = aionotify.Watcher()
        watcher.watch(self.filename, aionotify.Flags.MODIFY | all_flags)
        await watcher.setup(asyncio.get_event_loop())
        while True:
            count = 0
            while line := await f.readline():
                yield line
                count += 1
            if self.rewind and not count:
                await self.seek_to_end(f)
            logger.debug("Waiting for event")
            event = await watcher.get_event()
            logger.debug("Event: %r", event)
            logger.debug("Event flags: %r", event.flags)

            if event.flags & aionotify.Flags.ACCESS:
                logger.debug("Access event")
            if event.flags & aionotify.Flags.ATTRIB:
                logger.debug("Attrib event")
            if event.flags & aionotify.Flags.CLOSE_WRITE:
                logger.debug("Close write event")
            if event.flags & aionotify.Flags.CLOSE_NOWRITE:
                logger.debug("Close no write event")
            if event.flags & aionotify.Flags.CREATE:
                logger.debug("Create event")
            if event.flags & aionotify.Flags.DELETE:
                logger.debug("Delete event")
            if event.flags & aionotify.Flags.DELETE_SELF:
                logger.debug("Delete self event")
            if event.flags & aionotify.Flags.MODIFY:
                logger.debug("Modify event")
            if event.flags & aionotify.Flags.MOVE_SELF:
                logger.debug("Move self event")
            if event.flags & aionotify.Flags.MOVED_FROM:
                logger.debug("Moved from event")
            if event.flags & aionotify.Flags.MOVED_TO:
                logger.debug("Moved to event")
            if event.flags & aionotify.Flags.OPEN:
                logger.debug("Open event")

            if event.flags & removed_flags:
                logger.debug("File removed")
                break
    finally:
        self.close_watcher(watcher)

import discord
import asyncio
import shutil
import aiohttp
import datetime
import time
from models import Channel, Raiders, Role, Ban, session


class BotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super(BotClient, self).__init__(*args, **kwargs)
        self.commands = {
            'ping' : self.ping,
            'allow' : self.allow,
            'view' : self.view,
            'help' : self.help
        }

        self.colours = {
            'server' : 0xfc0303
        }

        self.prefix = '!'

    async def on_ready(self):
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')
        await client.change_presence(activity=discord.Game(name='Looking for Raids'))


    async def ping(self, message, stripped):
        t = message.created_at.timestamp()
        e = await message.channel.send('pong')
        delta = e.created_at.timestamp() - t

        await e.edit(content='Pong! {}ms round trip'.format(round(delta * 1000)))


    async def on_message(self, message):
        if message.author.bot:
            return

        raider = session.query(Raiders).filter_by(userId=message.author.id).first()
        if raider is not None:
            await message.delete()
            return

        await self.getCommand(message)


    async def getCommand(self, message):
        if message.content[0:len(self.prefix)] == self.prefix:
            command = (message.content + ' ')[len(self.prefix):message.content.find(' ')]
            if command in self.commands:
                stripped = (message.content + ' ')[message.content.find(' '):].strip()
                await self.commands[command](message, stripped)
                return True
            return False


    async def on_guild_channel_delete(self, channel):

        async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
            latest = entry

        user = session.query(Channel).filter_by(userId=latest.user.id).first()
        if user is None:
            d = Channel(userId=latest.user.id, savedTime=(time.time() + 120), deleted=0)
            session.add(d)
            session.commit()
            user = session.query(Channel).filter_by(userId=latest.user.id).first()
        elif (user.savedTime - time.time()) <= 0:
            user.savedTime = (time.time() + 120)
            user.deleted = 0
            session.commit()
            user = session.query(Channel).filter_by(userId=latest.user.id).first()

        if (user.savedTime - time.time()) > 0:
            user.deleted = user.deleted + 1
            session.commit()
            user = session.query(Channel).filter_by(userId=latest.user.id).first()   

        if user.deleted == 3:
            d = Raiders(userId=latest.user.id, offense='Channel')
            session.add(d)
            session.delete(user)
            session.commit()
            member = channel.guild.get_member(user.userId)
            for role in member.roles[1:]:
                await member.remove_roles(role)
            role = discord.utils.get(channel.guild.roles, name="Under Investigation")
            await member.add_roles(role)


    async def on_guild_role_delete(self, channel):

        async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
            latest = entry

        user = session.query(Role).filter_by(userId=latest.user.id).first()
        if user is None:
            d = Role(userId=latest.user.id, savedTime=(time.time() + 120), deleted=0)
            session.add(d)
            session.commit()
            user = session.query(Role).filter_by(userId=latest.user.id).first()
        elif (user.savedTime - time.time()) <= 0:
            user.savedTime = (time.time() + 120)
            user.deleted = 0
            session.commit()
            user = session.query(Role).filter_by(userId=latest.user.id).first()

        if (user.savedTime - time.time()) > 0:
            user.deleted = user.deleted + 1
            session.commit()
            user = session.query(Role).filter_by(userId=latest.user.id).first()   

        if user.deleted == 5:
            d = Raiders(userId=latest.user.id, offense='Role')
            session.add(d)
            session.delete(user)
            session.commit()
            member = channel.guild.get_member(user.userId)
            for role in member.roles[1:]:
                await member.remove_roles(role)
            role = discord.utils.get(channel.guild.roles, name="Under Investigation")
            await member.add_roles(role)


    async def on_member_ban(self, guild, user):

        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            latest = entry

        user = session.query(Ban).filter_by(userId=latest.user.id).first()
        if user is None:
            d = Ban(userId=latest.user.id, savedTime=(time.time() + 120), deleted=0)
            session.add(d)
            session.commit()
            user = session.query(Ban).filter_by(userId=latest.user.id).first()
        elif (user.savedTime - time.time()) <= 0:
            user.savedTime = (time.time() + 60)
            user.deleted = 0
            session.commit()
            user = session.query(Ban).filter_by(userId=latest.user.id).first()

        if (user.savedTime - time.time()) > 0:
            user.deleted = user.deleted + 1
            session.commit()
            user = session.query(Ban).filter_by(userId=latest.user.id).first()   

        if user.deleted == 3:
            d = Raiders(userId=latest.user.id, offense='Ban')
            session.add(d)
            session.delete(user)
            session.commit()
            member = guild.get_member(user.userId)
            for role in member.roles[1:]:
                await member.remove_roles(role)
            role = discord.utils.get(guild.roles, name="Under Investigation")
            await member.add_roles(role)


    async def allow(self, message, stripped):
        if message.author.guild_permissions.administrator:
            members = [x.id for x in message.mentions]
            for member in members:
                user = session.query(Raiders).filter_by(userId=member).first()
                if user is not None:
                    session.delete(user)
                    session.commit()
                    member = message.guild.get_member(user.userId)
                    role = discord.utils.get(message.guild.roles, name="Under Investigation")
                    await member.remove_roles(role)
                else:
                    pass

    async def view(self, message, stripped):
        if message.author.guild_permissions.administrator:
            query = session.query(Raiders)
            name = []
            reason = []
            for record in query:
                member = message.guild.get_member(record.userId)
                name.append(member)
                reason.append(record.offense)

            j_name = '\n'.join(map(str, name))
            j_reason = '\n'.join(map(str, reason))

            embed = discord.Embed(title='Flagged Users', color=self.colours['server'])
            embed.add_field(name='Username', value=j_name, inline=True)
            embed.add_field(name='Offense', value=j_reason, inline=True)
            await message.channel.send(embed=embed)

    async def help(self, message, stripped):
        await message.channel.send('''
        **Help Menu**
!view - allows you to view a list of flagged users.
!allow @user - allows you to remove a user from flagged. 
        ''')
        

#with open('token', 'r') as token_f:
    #token = token_f.read().strip('\n')

client = BotClient()
client.run('')

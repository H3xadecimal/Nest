from discord.ext import commands
import traceback
import time
import textwrap

class AdminCommands(commands.Cog):
    @commands.is_owner()
    @commands.group()
    async def module(self, ctx):
        pass
        
    @module.command()
    async def reload(self, ctx, module: str):
        ctx.bot.reload_module(module)
        await ctx.send(f"Successfully reloaded {module}!")
    
    @commands.is_owner()
    @module.command()
    async def load(self, ctx, module: str):
        ctx.bot.load_module(module)
        await ctx.send(f"Successfully loaded {module}!")

    @commands.is_owner(usage='<code>')
    @commands.command()
    async def eval(self, ctx):
        if self._eval.get('env') is None:
            self._eval['env'] = {}
        if self._eval.get('count') is None:
            self._eval['count'] = 0

        self._eval['env'].update({
            'ctx': ctx,
            'message': ctx.msg,
            'channel': ctx.msg.channel,
            'guild': ctx.msg.guild,
            'server': ctx.msg.guild,
            'author': ctx.msg.author
        })

        # let's make this safe to work with
        code = ctx.suffix.replace('```py\n', '').replace('```', '').replace('`', '')
        _code = "async def func(self):\n  try:\n{}\n  finally:\n    self._eval['env'].update(locals())"\
                .format(textwrap.indent(code, '    '))
        before = time.monotonic()

        # noinspection PyBroadException
        try:
            exec(_code, self._eval['env'])

            func = self._eval['env']['func']
            output = await func(self)

            if output is not None:
                output = repr(output)
        except Exception as e:
            output = '{}: {}'.format(type(e).__name__, e)

        after = time.monotonic()
        self._eval['count'] += 1
        count = self._eval['count']
        code = code.split('\n')

        if len(code) == 1:
            _in = 'In [{}]: {}'.format(count, code[0])
        else:
            _first_line = code[0]
            _rest = code[1:]
            _rest = '\n'.join(_rest)
            _countlen = len(str(count)) + 2
            _rest = textwrap.indent(_rest, '...: ')
            _rest = textwrap.indent(_rest, ' ' * _countlen)
            _in = 'In [{}]: {}\n{}'.format(count, _first_line, _rest)

        message = '```py\n{}'.format(_in)
        ms = int(round((after - before) * 1000))

        if output is not None:
            message += '\nOut[{}]: {}'.format(count, output)

        if ms > 100:  # noticeable delay
            message += '\n# {} ms\n```'.format(ms)
        else:
            message += '\n```'

        try:
            if ctx.msg.author.id == ctx.user.id:
                await ctx.msg.edit(content=message)
            else:
                await ctx.send(message)
        except discord.HTTPException:
            await ctx.msg.channel.trigger_typing()
            await ctx.send('Output was too big to be printed.')
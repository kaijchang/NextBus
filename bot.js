const Discord = require('discord.js');
const Enmap = require('enmap');

const fs = require('fs');


const client = new Discord.Client();

const prefix = '!bus';

client.commands = {};
client.notifications = new Enmap();


fs.readdirSync('commands').forEach(command => {
    const cmd = require(`./commands/${command}`);
    const cmdName = command.split('.')[0];
    client.commands[cmdName] = cmd;
});

client.on('message', message => {
    if (message.author.bot) return;
    if (!message.guild) return;
    if (message.content.indexOf(prefix) !== 0) return;
    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const command = args.shift().toLowerCase();
    const cmd = client.commands[command];
    if (!cmd) return;
    cmd(client, message, args);
});


client.login(process.env.TOKEN)
    .then(() => console.log('Bot Up!'))
    .catch(console.log);

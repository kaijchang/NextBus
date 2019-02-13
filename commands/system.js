const Discord = require('discord.js');

const rp = require('request-promise');

module.exports = (client, message, args) => {
    rp('http://webservices.nextbus.com/service/publicJSONFeed?command=agencyList')
        .then(resp => {
            const embed = new Discord.RichEmbed()
                .setAuthor('NextBusBot', client.user.avatarURL)
                .setTitle('Search Results')
                .setTimestamp(new Date())
                .setColor(0x37980a);

            JSON.parse(resp)['agency'].filter(
                agency => agency['title'].toLowerCase().includes(args[0].toLowerCase())
            ).forEach(agency => {
                embed.addField(agency['title'], agency['tag']);
            });

            message.channel.send(embed);
        })
};

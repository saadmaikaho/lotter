const { DataTypes } = require('sequelize');
const { sequelize } = require('./database'); // Assuming you have a separate file for database configuration

const LotteryTicket = sequelize.define('LotteryTicket', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    ticket_code: {
        type: DataTypes.STRING(50),
        unique: true
    },
    result: {
        type: DataTypes.STRING(50),
        allowNull: true
    },
    used: {
        type: DataTypes.BOOLEAN,
        defaultValue: false
    },
    use_count: {
        type: DataTypes.INTEGER,
        defaultValue: 0
    }
});

const AdminUser = sequelize.define('AdminUser', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    username: {
        type: DataTypes.STRING(20),
        unique: true
    },
    password: {
        type: DataTypes.STRING(128)
    }
});

module.exports = {
    LotteryTicket,
    AdminUser
};

